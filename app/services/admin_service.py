from __future__ import annotations

from datetime import UTC, datetime
import logging
from pathlib import Path
from time import perf_counter
from uuid import UUID

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.admin.document_status import DocumentStatus
from app.admin.storage import DocumentStorage
from app.core.config import settings
from app.core.logging import get_logger, log_event
from app.integrations.dify import (
    DifyAuthError,
    DifyBadRequestError,
    DifyClientError,
    DifyConfigurationError,
    DifyFileTooLargeError,
    DifyServiceUnavailableError,
    DifyTimeoutError,
    DifyUnsupportedFileTypeError,
    get_dify_client,
)
from app.repositories.document_repo import DocumentRepository

logger = get_logger(__name__)


class AdminDocumentService:
    def __init__(self) -> None:
        self.document_repo = DocumentRepository()
        self.storage = DocumentStorage()
        self.dify_client = get_dify_client()

    def upload_document(self, db: Session, *, upload: UploadFile, admin_user_id: UUID) -> dict:
        self._validate_upload(upload)
        stored = self.storage.save(upload)
        filename = upload.filename or "untitled"
        now = datetime.now(UTC)

        doc = self.document_repo.create(
            db,
            filename=filename,
            source_type="upload",
            status=DocumentStatus.UPLOADED.value,
            uploaded_at=now,
            note=None,
            local_path=stored.local_path,
            source_uri=stored.local_path,
            created_by=admin_user_id,
            mime_type=stored.mime_type,
            content_type=stored.mime_type,
            file_size=stored.file_size,
            file_extension=stored.file_extension,
            dify_sync_status="not_synced",
            created_at=now,
        )
        db.commit()
        log_event(
            logger,
            logging.INFO,
            "document_uploaded",
            "success",
            document_id=str(doc.id),
            filename=doc.filename,
            local_path=doc.local_path,
            mime_type=doc.mime_type,
            file_size=doc.file_size,
        )
        return self._to_payload(doc)

    def list_documents(self, db: Session, *, limit: int, offset: int) -> dict:
        docs = self.document_repo.list_all(db, limit=limit, offset=offset)
        return {"items": [self._to_payload(doc) for doc in docs]}

    def get_document(self, db: Session, *, doc_id: UUID) -> dict:
        doc = self.document_repo.get_by_id(db, doc_id)
        if doc is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
        return self._to_payload(doc)

    def delete_document(self, db: Session, *, doc_id: UUID) -> None:
        doc = self.document_repo.get_by_id(db, doc_id)
        if doc is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
        try:
            self.storage.delete(doc.local_path or doc.source_uri)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
        self.document_repo.delete(db, doc=doc)
        db.commit()

    def trigger_graph_sync(self, db: Session, *, doc_id: UUID) -> dict:
        doc = self.document_repo.get_by_id(db, doc_id)
        if doc is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

        started_at = datetime.now(UTC)
        log_event(
            logger,
            logging.INFO,
            "document_sync_started",
            "started",
            document_id=str(doc.id),
            target_system="graph",
        )
        try:
            updated_doc = self.document_repo.update_status(
                db,
                doc=doc,
                status=DocumentStatus.GRAPH_PENDING.value,
            )
            updated_doc = self.document_repo.mark_synced(
                db,
                doc=updated_doc,
                target_system="graph",
                status=DocumentStatus.GRAPH_PENDING.value,
                synced_at=started_at,
            )
            updated_doc.note = "Graph sync queued for lightweight graph refresh"
            db.commit()
            log_event(
                logger,
                logging.INFO,
                "document_sync_succeeded",
                "success",
                document_id=str(updated_doc.id),
                target_system="graph",
                sync_status=updated_doc.status,
            )
            return {
                "document_id": updated_doc.id,
                "status": updated_doc.status,
                "target_system": "graph",
                "message": "Graph sync has been queued",
            }
        except Exception as exc:
            log_event(
                logger,
                logging.ERROR,
                "document_sync_failed",
                "failed",
                document_id=str(doc.id),
                target_system="graph",
                detail=str(exc),
            )
            raise

    async def trigger_dify_index(self, db: Session, *, doc_id: UUID) -> dict:
        doc = self.document_repo.get_by_id(db, doc_id)
        if doc is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
        if doc.dify_sync_status == "syncing":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Document is already syncing to Dify")
        if doc.synced_to_dify and doc.dify_upload_file_id:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Document already synced to Dify")

        local_path = doc.local_path or doc.source_uri
        started_at = datetime.now(UTC)
        started = perf_counter()

        log_event(
            logger,
            logging.INFO,
            "document_sync_started",
            "started",
            document_id=str(doc.id),
            filename=doc.filename,
            local_path=local_path,
            target_system="dify",
        )
        try:
            resolved_path = self._resolve_local_path(local_path)
            self.document_repo.mark_dify_syncing(db, doc=doc, synced_at=started_at)
            uploaded_file = await self.dify_client.upload_file(
                file_path=str(resolved_path),
                user=str(doc.id),
                mime_type=doc.mime_type or doc.content_type,
            )
            uploaded_at = self._to_datetime(uploaded_file.created_at)
            updated_doc = self.document_repo.mark_dify_synced(
                db,
                doc=doc,
                dify_upload_file_id=uploaded_file.file_id,
                dify_uploaded_at=uploaded_at,
                synced_at=datetime.now(UTC),
                note=f"Dify file uploaded: {uploaded_file.file_id}",
            )
            db.commit()
            elapsed_ms = round((perf_counter() - started) * 1000, 2)
            log_event(
                logger,
                logging.INFO,
                "document_sync_succeeded",
                "success",
                document_id=str(updated_doc.id),
                filename=updated_doc.filename,
                local_path=updated_doc.local_path,
                target_system="dify",
                dify_upload_file_id=uploaded_file.file_id,
                dify_sync_status=updated_doc.dify_sync_status,
                elapsed_ms=elapsed_ms,
            )
            return {
                "document_id": updated_doc.id,
                "status": updated_doc.status,
                "target_system": "dify",
                "message": updated_doc.note,
            }
        except DifyConfigurationError as exc:
            self._mark_dify_failure(
                db,
                doc=doc,
                error_code="dify_not_configured",
                error_message="Dify integration is not configured",
                started=started,
            )
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Dify integration is not configured",
            ) from exc
        except DifyClientError as exc:
            mapped = self._map_dify_sync_exception(exc)
            self._mark_dify_failure(
                db,
                doc=doc,
                error_code=mapped["error_code"],
                error_message=mapped["detail"],
                started=started,
            )
            raise HTTPException(
                status_code=mapped["status_code"],
                detail=mapped["detail"],
            ) from exc
        except HTTPException as exc:
            self._mark_dify_failure(
                db,
                doc=doc,
                error_code="local_file_missing" if exc.status_code == status.HTTP_404_NOT_FOUND else "invalid_local_file",
                error_message=exc.detail,
                started=started,
            )
            raise
        except Exception as exc:
            self._mark_dify_failure(
                db,
                doc=doc,
                error_code="unexpected_error",
                error_message="Unexpected Dify sync failure",
                started=started,
            )
            log_event(
                logger,
                logging.ERROR,
                "document_sync_failed",
                "failed",
                document_id=str(doc.id),
                filename=doc.filename,
                local_path=local_path,
                target_system="dify",
                detail=str(exc),
            )
            raise

    def _to_payload(self, doc) -> dict:
        return {
            "id": doc.id,
            "filename": doc.filename,
            "status": doc.status,
            "source_type": doc.source_type,
            "uploaded_at": doc.uploaded_at,
            "synced_to_dify": doc.synced_to_dify,
            "synced_to_graph": doc.synced_to_graph,
            "note": doc.note,
            "local_path": doc.local_path,
            "source_uri": doc.source_uri,
            "mime_type": doc.mime_type,
            "content_type": doc.content_type,
            "file_size": doc.file_size,
            "file_extension": doc.file_extension,
            "dify_upload_file_id": doc.dify_upload_file_id,
            "dify_uploaded_at": doc.dify_uploaded_at,
            "dify_sync_status": doc.dify_sync_status,
            "dify_error_code": doc.dify_error_code,
            "dify_error_message": doc.dify_error_message,
            "created_by": doc.created_by,
            "created_at": doc.created_at,
            "last_sync_target": doc.last_sync_target,
            "last_sync_status": doc.last_sync_status,
            "last_sync_at": doc.last_sync_at,
            "dify_file_input_variable": settings.DIFY_FILE_INPUT_VARIABLE,
            "dify_workflow_file_input": self._build_dify_workflow_file_input(doc),
        }

    def _validate_upload(self, upload: UploadFile) -> None:
        filename = (upload.filename or "").strip()
        if not filename:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file must have a filename")

        upload.file.seek(0, 2)
        file_size = upload.file.tell()
        upload.file.seek(0)

        if file_size <= 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty")
        if file_size > settings.DOCUMENT_MAX_FILE_SIZE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="Uploaded file exceeds local size limit",
            )

        suffix = Path(filename).suffix.lower().lstrip(".")
        allowed_extensions = settings.document_allowed_extensions
        if allowed_extensions and suffix not in allowed_extensions:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file type is not allowed")

        mime_type = (upload.content_type or "").lower()
        allowed_mime_types = settings.document_allowed_mime_types
        if allowed_mime_types and mime_type and mime_type not in allowed_mime_types:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded MIME type is not allowed")

    @staticmethod
    def _to_datetime(value: int | None) -> datetime | None:
        if value is None:
            return None
        return datetime.fromtimestamp(value, tz=UTC)

    @staticmethod
    def _resolve_local_path(local_path: str | None) -> Path:
        if not local_path:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Document has no local file path")
        path = Path(local_path).expanduser()
        if not path.exists() or not path.is_file():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Local document file does not exist")
        return path

    def _mark_dify_failure(
        self,
        db: Session,
        *,
        doc,
        error_code: str | None,
        error_message: str,
        started: float,
    ) -> None:
        synced_at = datetime.now(UTC)
        updated_doc = self.document_repo.mark_dify_failed(
            db,
            doc=doc,
            error_code=error_code,
            error_message=error_message,
            synced_at=synced_at,
            note=error_message,
        )
        db.commit()
        elapsed_ms = round((perf_counter() - started) * 1000, 2)
        log_event(
            logger,
            logging.WARNING,
            "document_sync_failed",
            "failed",
            document_id=str(updated_doc.id),
            filename=updated_doc.filename,
            local_path=updated_doc.local_path,
            target_system="dify",
            dify_sync_status=updated_doc.dify_sync_status,
            error_code=error_code,
            error_message=error_message,
            elapsed_ms=elapsed_ms,
        )

    @staticmethod
    def _map_dify_sync_exception(exc: DifyClientError) -> dict[str, str | int]:
        error_code = getattr(exc, "error_code", None)
        if isinstance(exc, DifyFileTooLargeError) or error_code == "file_too_large":
            return {"status_code": status.HTTP_400_BAD_REQUEST, "detail": "Dify rejected the file as too large", "error_code": "file_too_large"}
        if isinstance(exc, DifyUnsupportedFileTypeError) or error_code == "unsupported_file_type":
            return {
                "status_code": status.HTTP_400_BAD_REQUEST,
                "detail": "Dify does not support this file type",
                "error_code": "unsupported_file_type",
            }
        if isinstance(exc, DifyAuthError):
            return {"status_code": status.HTTP_502_BAD_GATEWAY, "detail": "Dify authentication failed", "error_code": "dify_auth_failed"}
        if isinstance(exc, DifyTimeoutError):
            return {"status_code": status.HTTP_504_GATEWAY_TIMEOUT, "detail": "Dify request timed out", "error_code": "dify_timeout"}
        if isinstance(exc, DifyServiceUnavailableError):
            return {"status_code": status.HTTP_502_BAD_GATEWAY, "detail": "Dify service is unavailable", "error_code": "dify_service_unavailable"}
        if isinstance(exc, DifyBadRequestError) and error_code == "no_file_uploaded":
            return {"status_code": status.HTTP_400_BAD_REQUEST, "detail": "Dify did not receive the uploaded file", "error_code": "no_file_uploaded"}
        if isinstance(exc, DifyBadRequestError) and error_code == "too_many_files":
            return {"status_code": status.HTTP_400_BAD_REQUEST, "detail": "Dify rejected the request because too many files were provided", "error_code": "too_many_files"}
        return {"status_code": status.HTTP_502_BAD_GATEWAY, "detail": "Dify file upload failed", "error_code": error_code or "dify_upload_failed"}

    def _build_dify_workflow_file_input(self, doc) -> dict | None:
        if not settings.DIFY_FILE_INPUT_VARIABLE or not doc.dify_upload_file_id:
            return None
        return {
            settings.DIFY_FILE_INPUT_VARIABLE: [
                {
                    "transfer_method": "local_file",
                    "upload_file_id": doc.dify_upload_file_id,
                    "type": "document",
                }
            ]
        }

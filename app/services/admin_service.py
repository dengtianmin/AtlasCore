from __future__ import annotations

from datetime import UTC, datetime
import logging
from uuid import UUID

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.admin.document_status import DocumentStatus
from app.admin.storage import DocumentStorage
from app.core.logging import get_logger, log_event
from app.integrations.dify import DifyClientError, DifyConfigurationError, get_dify_client
from app.repositories.document_repo import DocumentRepository

logger = get_logger(__name__)


class AdminDocumentService:
    def __init__(self) -> None:
        self.document_repo = DocumentRepository()
        self.storage = DocumentStorage()
        self.dify_client = get_dify_client()

    def upload_document(self, db: Session, *, upload: UploadFile, admin_user_id: UUID) -> dict:
        source_uri, file_size = self.storage.save(upload)
        filename = upload.filename or "untitled"
        now = datetime.now(UTC)

        doc = self.document_repo.create(
            db,
            filename=filename,
            source_type="upload",
            status=DocumentStatus.UPLOADED.value,
            uploaded_at=now,
            source_uri=source_uri,
            created_by=admin_user_id,
            content_type=upload.content_type,
            file_size=file_size,
            created_at=now,
        )
        db.commit()
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

        log_event(
            logger,
            logging.INFO,
            "document_sync_started",
            "started",
            document_id=str(doc.id),
            target_system="dify",
        )
        try:
            uploaded_file = await self.dify_client.upload_file(
                file_path=str(doc.source_uri or ""),
                user=str(doc.id),
                mime_type=doc.content_type,
            )
            updated_doc = self.document_repo.mark_synced(
                db,
                doc=doc,
                target_system="dify",
                status=DocumentStatus.INDEXED.value,
                synced_at=datetime.now(UTC),
            )
            updated_doc.note = f"Dify file uploaded: {uploaded_file.file_id}"
            db.commit()
            log_event(
                logger,
                logging.INFO,
                "document_sync_succeeded",
                "success",
                document_id=str(updated_doc.id),
                target_system="dify",
                sync_status=updated_doc.status,
                provider_file_id=uploaded_file.file_id,
            )
            return {
                "document_id": updated_doc.id,
                "status": updated_doc.status,
                "target_system": "dify",
                "message": updated_doc.note,
            }
        except DifyConfigurationError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Dify integration is not configured",
            ) from exc
        except DifyClientError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Dify file upload failed",
            ) from exc
        except Exception as exc:
            log_event(
                logger,
                logging.ERROR,
                "document_sync_failed",
                "failed",
                document_id=str(doc.id),
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
            "source_uri": doc.source_uri,
            "content_type": doc.content_type,
            "file_size": doc.file_size,
            "created_by": doc.created_by,
            "created_at": doc.created_at,
            "last_sync_target": doc.last_sync_target,
            "last_sync_status": doc.last_sync_status,
            "last_sync_at": doc.last_sync_at,
        }

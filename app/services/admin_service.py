from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.admin.document_status import DocumentStatus
from app.admin.storage import DocumentStorage
from app.integrations.dify import DifyDocumentIndexRequest, get_dify_client
from app.repositories.document_repo import DocumentRepository


class AdminDocumentService:
    def __init__(self) -> None:
        self.document_repo = DocumentRepository()
        self.storage = DocumentStorage()
        self.dify_client = get_dify_client()

    def upload_document(self, db: Session, *, upload: UploadFile, admin_user_id: UUID) -> dict:
        source_uri, file_size = self.storage.save(upload)
        filename = upload.filename or "untitled"

        doc = self.document_repo.create(
            db,
            filename=filename,
            source_type="upload",
            status=DocumentStatus.UPLOADED.value,
            uploaded_at=datetime.now(UTC),
            source_uri=source_uri,
            created_by=admin_user_id,
            content_type=upload.content_type,
            file_size=file_size,
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
        )
        db.commit()
        return {
            "document_id": updated_doc.id,
            "status": updated_doc.status,
            "target_system": "graph",
            "message": "Graph sync has been queued",
        }

    def trigger_dify_index(self, db: Session, *, doc_id: UUID) -> dict:
        doc = self.document_repo.get_by_id(db, doc_id)
        if doc is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

        dify_job = self.dify_client.enqueue_document_index(
            DifyDocumentIndexRequest(
                document_id=str(doc.id),
                title=doc.filename,
                source_uri=doc.source_uri,
            )
        )
        updated_doc = self.document_repo.mark_synced(
            db,
            doc=doc,
            target_system="dify",
            status=DocumentStatus.INDEXED.value,
        )
        db.commit()
        return {
            "document_id": updated_doc.id,
            "status": updated_doc.status,
            "target_system": "dify",
            "message": dify_job.message,
        }

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
        }

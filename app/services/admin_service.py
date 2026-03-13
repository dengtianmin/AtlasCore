from uuid import UUID

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.admin.document_status import DocumentStatus
from app.admin.storage import DocumentStorage
from app.integrations.dify import DifyDocumentIndexRequest, get_dify_client
from app.repositories.document_repo import DocumentRepository
from app.repositories.sync_repo import SyncRecordRepository


class AdminDocumentService:
    def __init__(self) -> None:
        self.document_repo = DocumentRepository()
        self.sync_repo = SyncRecordRepository()
        self.storage = DocumentStorage()
        self.dify_client = get_dify_client()

    def upload_document(self, db: Session, *, upload: UploadFile, admin_user_id: UUID) -> dict:
        source_uri, file_size = self.storage.save(upload)
        title = upload.filename or "untitled"

        doc = self.document_repo.create(
            db,
            title=title,
            source_type="upload",
            source_uri=source_uri,
            status=DocumentStatus.UPLOADED.value,
            created_by=admin_user_id,
            file_name=upload.filename,
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
        sync_record = self.sync_repo.create(
            db,
            document_id=doc.id,
            target_system="graph",
            sync_status="queued",
        )
        db.commit()
        return {
            "document_id": updated_doc.id,
            "status": updated_doc.status,
            "sync_record_id": sync_record.id,
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
                title=doc.title,
                source_uri=doc.source_uri,
            )
        )
        updated_doc = self.document_repo.update_status(
            db,
            doc=doc,
            status=DocumentStatus.INDEXED.value,
        )
        sync_record = self.sync_repo.create(
            db,
            document_id=doc.id,
            target_system="dify",
            sync_status=dify_job.status,
            external_id=dify_job.job_id,
        )
        db.commit()
        return {
            "document_id": updated_doc.id,
            "status": updated_doc.status,
            "sync_record_id": sync_record.id,
            "target_system": "dify",
            "message": dify_job.message,
        }

    def _to_payload(self, doc) -> dict:
        return {
            "id": doc.id,
            "title": doc.title,
            "status": doc.status,
            "source_type": doc.source_type,
            "source_uri": doc.source_uri,
            "file_name": doc.file_name,
            "content_type": doc.content_type,
            "file_size": doc.file_size,
            "created_by": doc.created_by,
            "created_at": doc.created_at,
            "updated_at": doc.updated_at,
        }

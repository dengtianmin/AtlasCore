from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.document import Document


class DocumentRepository:
    def create(
        self,
        db: Session,
        *,
        filename: str,
        file_type: str,
        source_type: str,
        status: str,
        uploaded_at: datetime,
        synced_to_dify: bool = False,
        synced_to_graph: bool = False,
        note: str | None = None,
        local_path: str | None = None,
        source_uri: str | None = None,
        created_by: UUID | None,
        mime_type: str | None,
        content_type: str | None,
        file_size: int | None,
        file_extension: str | None,
        dify_sync_status: str | None = None,
        created_at: datetime,
    ) -> Document:
        doc = Document(
            filename=filename,
            file_type=file_type,
            source_type=source_type,
            status=status,
            uploaded_at=uploaded_at,
            synced_to_dify=synced_to_dify,
            synced_to_graph=synced_to_graph,
            note=note,
            local_path=local_path,
            source_uri=source_uri,
            created_by=created_by,
            mime_type=mime_type,
            content_type=content_type,
            file_size=file_size,
            file_extension=file_extension,
            dify_sync_status=dify_sync_status,
            created_at=created_at,
        )
        db.add(doc)
        db.flush()
        db.refresh(doc)
        return doc

    def get_by_id(self, db: Session, doc_id: UUID) -> Document | None:
        stmt = select(Document).where(Document.id == doc_id)
        return db.execute(stmt).scalar_one_or_none()

    def list_all(self, db: Session, *, limit: int = 50, offset: int = 0) -> list[Document]:
        stmt = (
            select(Document)
            .order_by(Document.uploaded_at.desc(), Document.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(db.execute(stmt).scalars().all())

    def list_by_file_type(
        self,
        db: Session,
        *,
        file_type: str,
        limit: int = 50,
        offset: int = 0,
        active_only: bool = False,
    ) -> list[Document]:
        stmt = select(Document).where(Document.file_type == file_type)
        if active_only:
            stmt = stmt.where(Document.is_active.is_(True))
        stmt = stmt.order_by(Document.uploaded_at.desc(), Document.created_at.desc()).limit(limit).offset(offset)
        return list(db.execute(stmt).scalars().all())

    def list_by_ids(self, db: Session, *, document_ids: list[UUID]) -> list[Document]:
        if not document_ids:
            return []
        stmt = select(Document).where(Document.id.in_(document_ids))
        return list(db.execute(stmt).scalars().all())

    def update_status(self, db: Session, *, doc: Document, status: str) -> Document:
        doc.status = status
        db.add(doc)
        db.flush()
        db.refresh(doc)
        return doc

    def mark_synced(
        self,
        db: Session,
        *,
        doc: Document,
        target_system: str,
        status: str,
        synced_at: datetime,
    ) -> Document:
        doc.status = status
        doc.last_sync_target = target_system
        doc.last_sync_status = status
        doc.last_sync_at = synced_at
        if target_system == "dify":
            doc.synced_to_dify = True
        if target_system == "graph":
            doc.synced_to_graph = True
        db.add(doc)
        db.flush()
        db.refresh(doc)
        return doc

    def delete(self, db: Session, *, doc: Document) -> None:
        db.delete(doc)
        db.flush()

    def save(self, db: Session, *, doc: Document) -> Document:
        db.add(doc)
        db.flush()
        db.refresh(doc)
        return doc

    def mark_dify_syncing(self, db: Session, *, doc: Document, synced_at: datetime) -> Document:
        doc.status = "syncing"
        doc.dify_sync_status = "syncing"
        doc.dify_error_code = None
        doc.dify_error_message = None
        doc.note = None
        doc.last_sync_target = "dify"
        doc.last_sync_status = "syncing"
        doc.last_sync_at = synced_at
        db.add(doc)
        db.flush()
        db.refresh(doc)
        return doc

    def mark_dify_synced(
        self,
        db: Session,
        *,
        doc: Document,
        dify_upload_file_id: str,
        dify_uploaded_at: datetime | None,
        synced_at: datetime,
        note: str,
    ) -> Document:
        doc.status = "synced"
        doc.synced_to_dify = True
        doc.dify_sync_status = "synced"
        doc.dify_upload_file_id = dify_upload_file_id
        doc.dify_uploaded_at = dify_uploaded_at
        doc.dify_error_code = None
        doc.dify_error_message = None
        doc.note = note
        doc.last_sync_target = "dify"
        doc.last_sync_status = "synced"
        doc.last_sync_at = synced_at
        db.add(doc)
        db.flush()
        db.refresh(doc)
        return doc

    def mark_dify_failed(
        self,
        db: Session,
        *,
        doc: Document,
        error_code: str | None,
        error_message: str,
        synced_at: datetime,
        note: str,
    ) -> Document:
        doc.status = "failed"
        doc.synced_to_dify = False
        doc.dify_sync_status = "failed"
        doc.dify_error_code = error_code
        doc.dify_error_message = error_message
        doc.note = note
        doc.last_sync_target = "dify"
        doc.last_sync_status = "failed"
        doc.last_sync_at = synced_at
        db.add(doc)
        db.flush()
        db.refresh(doc)
        return doc

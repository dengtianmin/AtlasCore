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
        source_type: str,
        status: str,
        uploaded_at: datetime,
        synced_to_dify: bool = False,
        synced_to_graph: bool = False,
        note: str | None = None,
        source_uri: str | None = None,
        created_by: UUID | None,
        content_type: str | None,
        file_size: int | None,
    ) -> Document:
        doc = Document(
            filename=filename,
            source_type=source_type,
            status=status,
            uploaded_at=uploaded_at,
            synced_to_dify=synced_to_dify,
            synced_to_graph=synced_to_graph,
            note=note,
            source_uri=source_uri,
            created_by=created_by,
            content_type=content_type,
            file_size=file_size,
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
            .order_by(Document.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
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
    ) -> Document:
        doc.status = status
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

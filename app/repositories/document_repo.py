from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.document import Document


class DocumentRepository:
    def create(
        self,
        db: Session,
        *,
        title: str,
        source_type: str,
        source_uri: str | None,
        status: str,
        created_by: UUID | None,
        file_name: str | None,
        content_type: str | None,
        file_size: int | None,
    ) -> Document:
        doc = Document(
            title=title,
            source_type=source_type,
            source_uri=source_uri,
            status=status,
            created_by=created_by,
            file_name=file_name,
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

    def delete(self, db: Session, *, doc: Document) -> None:
        db.delete(doc)
        db.flush()

from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.graph_extraction_task import GraphExtractionTask


class GraphExtractionTaskRepository:
    def create(self, db: Session, *, task: GraphExtractionTask) -> GraphExtractionTask:
        db.add(task)
        db.flush()
        db.refresh(task)
        return task

    def get_by_id(self, db: Session, *, task_id: UUID) -> GraphExtractionTask | None:
        stmt = select(GraphExtractionTask).where(GraphExtractionTask.id == task_id)
        return db.execute(stmt).scalar_one_or_none()

    def list_recent(self, db: Session, *, limit: int = 20, offset: int = 0) -> list[GraphExtractionTask]:
        stmt = (
            select(GraphExtractionTask)
            .order_by(GraphExtractionTask.created_at.desc(), GraphExtractionTask.updated_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(db.execute(stmt).scalars().all())

    def save(self, db: Session, *, task: GraphExtractionTask) -> GraphExtractionTask:
        db.add(task)
        db.flush()
        db.refresh(task)
        return task

    def delete_all(self, db: Session) -> None:
        db.execute(delete(GraphExtractionTask))
        db.flush()

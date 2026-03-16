from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.feedback_record import FeedbackRecord


class FeedbackRepository:
    def create(
        self,
        db: Session,
        *,
        qa_log_id: UUID,
        rating: int | None,
        liked: bool | None,
        comment: str | None,
        source: str,
        created_at: datetime,
    ) -> FeedbackRecord:
        record = FeedbackRecord(
            qa_log_id=qa_log_id,
            rating=rating,
            liked=liked,
            comment=comment,
            source=source,
            created_at=created_at,
        )
        db.add(record)
        db.flush()
        db.refresh(record)
        return record

    def list_by_qa_log(self, db: Session, *, qa_log_id: UUID) -> list[FeedbackRecord]:
        stmt = (
            select(FeedbackRecord)
            .where(FeedbackRecord.qa_log_id == qa_log_id)
            .order_by(FeedbackRecord.created_at.desc())
        )
        return list(db.execute(stmt).scalars().all())

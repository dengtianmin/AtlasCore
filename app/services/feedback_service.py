from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.feedback_repo import FeedbackRepository
from app.repositories.qa_log_repo import QuestionAnswerLogRepository


class FeedbackService:
    def __init__(self) -> None:
        self.feedback_repo = FeedbackRepository()
        self.qa_log_repo = QuestionAnswerLogRepository()

    def create_feedback(
        self,
        db: Session,
        *,
        qa_log_id: UUID,
        rating: int | None,
        liked: bool | None,
        comment: str | None,
        source: str,
    ) -> dict:
        if rating is None and liked is None and not comment:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Feedback is empty")

        qa_log = self.qa_log_repo.get_by_id(db, qa_log_id)
        if qa_log is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="QA log not found")

        record = self.feedback_repo.create(
            db,
            qa_log_id=qa_log_id,
            rating=rating,
            liked=liked,
            comment=comment,
            source=source,
            created_at=datetime.now(UTC),
        )
        db.commit()
        return self._to_payload(record)

    def list_feedback(self, db: Session, *, qa_log_id: UUID) -> dict:
        qa_log = self.qa_log_repo.get_by_id(db, qa_log_id)
        if qa_log is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="QA log not found")

        records = self.feedback_repo.list_by_qa_log(db, qa_log_id=qa_log_id)
        return {"items": [self._to_payload(record) for record in records]}

    def _to_payload(self, record) -> dict:
        return {
            "id": record.id,
            "qa_log_id": record.qa_log_id,
            "rating": record.rating,
            "liked": record.liked,
            "comment": record.comment,
            "source": record.source,
            "created_at": record.created_at,
        }

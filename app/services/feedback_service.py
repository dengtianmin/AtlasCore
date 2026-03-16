from datetime import UTC, datetime
import logging
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.logging import get_logger, log_event
from app.repositories.feedback_repo import FeedbackRepository
from app.repositories.qa_log_repo import QuestionAnswerLogRepository

logger = get_logger(__name__)


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
        payload = self._to_payload(record)
        log_event(
            logger,
            logging.INFO,
            "feedback_written",
            "success",
            qa_log_id=str(qa_log_id),
            feedback_id=str(payload["id"]),
            source=payload["source"],
        )
        return payload

    def list_feedback(self, db: Session, *, qa_log_id: UUID) -> dict:
        qa_log = self.qa_log_repo.get_by_id(db, qa_log_id)
        if qa_log is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="QA log not found")

        records = self.feedback_repo.list_by_qa_log(db, qa_log_id=qa_log_id)
        return {"items": [self._to_payload(record) for record in records]}

    def list_all_feedback(self, db: Session, *, limit: int, offset: int) -> dict:
        records = self.feedback_repo.list_all(db, limit=limit, offset=offset)
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

from datetime import datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.services.feedback_service import FeedbackService
from app.services.qa_log_service import QuestionAnswerLogService


class AdminLogService:
    def __init__(self) -> None:
        self.qa_log_service = QuestionAnswerLogService()
        self.feedback_service = FeedbackService()

    def list_logs(
        self,
        db: Session,
        *,
        limit: int,
        offset: int,
        keyword: str | None,
        source: str | None,
        liked: bool | None,
        rating: int | None,
        date_from: datetime | None,
        date_to: datetime | None,
    ) -> dict:
        base = self.qa_log_service.list_logs(db, limit=500, offset=0)["items"]
        filtered: list[dict] = []

        for record in base:
            if source and record["source"] != source:
                continue
            if keyword:
                haystack = " ".join(
                    part for part in [record["question"], record["answer"], record["retrieved_context"]] if part
                ).lower()
                if keyword.lower() not in haystack:
                    continue
            if date_from and record["created_at"] < date_from:
                continue
            if date_to and record["created_at"] > date_to:
                continue

            feedback_items = self.feedback_service.list_feedback(db, qa_log_id=record["id"])["items"]
            latest_feedback = feedback_items[0] if feedback_items else None
            if liked is not None and (latest_feedback is None or latest_feedback["liked"] is not liked):
                continue
            if rating is not None and (latest_feedback is None or latest_feedback["rating"] != rating):
                continue
            filtered.append(
                {
                    **record,
                    "feedback": latest_feedback,
                    "feedback_count": len(feedback_items),
                }
            )

        return {"items": filtered[offset : offset + limit]}

    def get_log(self, db: Session, *, record_id: UUID) -> dict:
        record = self.qa_log_service.get_log(db, record_id=record_id)
        if record is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="QA log not found")
        feedback_items = self.feedback_service.list_feedback(db, qa_log_id=record_id)["items"]
        latest_feedback = feedback_items[0] if feedback_items else None
        return {**record, "feedback": latest_feedback, "feedback_count": len(feedback_items)}

    def list_feedback(self, db: Session, *, limit: int, offset: int) -> dict:
        return self.feedback_service.list_all_feedback(db, limit=limit, offset=offset)

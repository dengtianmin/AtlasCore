from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.review_log import ReviewLog


class ReviewLogRepository:
    def create(
        self,
        db: Session,
        *,
        user_id: UUID | None,
        student_id_snapshot: str | None,
        name_snapshot: str | None,
        review_input: str,
        review_result: str | None,
        raw_response: str | None,
        normalized_result: str | None,
        parse_status: str,
        score: int | None,
        risk_level: str | None,
        engine_source: str,
        app_mode: str | None,
        workflow_run_id: str | None,
        provider_message_id: str | None,
        created_at: datetime,
    ) -> ReviewLog:
        record = ReviewLog(
            user_id=user_id,
            student_id_snapshot=student_id_snapshot,
            name_snapshot=name_snapshot,
            review_input=review_input,
            review_result=review_result,
            raw_response=raw_response,
            normalized_result=normalized_result,
            parse_status=parse_status,
            score=score,
            risk_level=risk_level,
            engine_source=engine_source,
            app_mode=app_mode,
            workflow_run_id=workflow_run_id,
            provider_message_id=provider_message_id,
            created_at=created_at,
        )
        db.add(record)
        db.flush()
        db.refresh(record)
        return record

    def get_by_id(self, db: Session, record_id: UUID) -> ReviewLog | None:
        stmt = select(ReviewLog).where(ReviewLog.id == record_id)
        return db.execute(stmt).scalar_one_or_none()

    def list_all(self, db: Session, *, limit: int = 50, offset: int = 0) -> list[ReviewLog]:
        stmt = select(ReviewLog).order_by(ReviewLog.created_at.desc()).limit(limit).offset(offset)
        return list(db.execute(stmt).scalars().all())

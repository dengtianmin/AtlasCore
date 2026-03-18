from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.qa_log import QuestionAnswerLog


class QuestionAnswerLogRepository:
    def create(
        self,
        db: Session,
        *,
        question: str,
        retrieved_context: str | None,
        answer: str,
        created_at: datetime,
        user_id: UUID | None,
        student_id_snapshot: str | None,
        name_snapshot: str | None,
        session_id: str | None,
        source: str,
        status: str,
        provider_message_id: str | None,
        error_code: str | None,
    ) -> QuestionAnswerLog:
        record = QuestionAnswerLog(
            question=question,
            retrieved_context=retrieved_context,
            answer=answer,
            created_at=created_at,
            user_id=user_id,
            student_id_snapshot=student_id_snapshot,
            name_snapshot=name_snapshot,
            session_id=session_id,
            source=source,
            status=status,
            provider_message_id=provider_message_id,
            error_code=error_code,
        )
        db.add(record)
        db.flush()
        db.refresh(record)
        return record

    def get_by_id(self, db: Session, record_id: UUID) -> QuestionAnswerLog | None:
        stmt = select(QuestionAnswerLog).where(QuestionAnswerLog.id == record_id)
        return db.execute(stmt).scalar_one_or_none()

    def list_all(self, db: Session, *, limit: int = 50, offset: int = 0) -> list[QuestionAnswerLog]:
        stmt = (
            select(QuestionAnswerLog)
            .order_by(QuestionAnswerLog.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(db.execute(stmt).scalars().all())

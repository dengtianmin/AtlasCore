from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.repositories.qa_log_repo import QuestionAnswerLogRepository


class QuestionAnswerLogService:
    def __init__(self) -> None:
        self.qa_log_repo = QuestionAnswerLogRepository()

    def create_log(
        self,
        db: Session,
        *,
        question: str,
        retrieved_context: str | None,
        answer: str,
        rating: int | None,
        liked: bool | None,
        session_id: str | None,
        source: str,
    ) -> dict:
        record = self.qa_log_repo.create(
            db,
            question=question,
            retrieved_context=retrieved_context,
            answer=answer,
            rating=rating,
            liked=liked,
            created_at=datetime.now(UTC),
            session_id=session_id,
            source=source,
        )
        db.commit()
        return self._to_payload(record)

    def list_logs(self, db: Session, *, limit: int, offset: int) -> dict:
        records = self.qa_log_repo.list_all(db, limit=limit, offset=offset)
        return {"items": [self._to_payload(record) for record in records]}

    def get_log(self, db: Session, *, record_id: UUID) -> dict | None:
        record = self.qa_log_repo.get_by_id(db, record_id)
        if record is None:
            return None
        return self._to_payload(record)

    def _to_payload(self, record) -> dict:
        return {
            "id": record.id,
            "question": record.question,
            "retrieved_context": record.retrieved_context,
            "answer": record.answer,
            "rating": record.rating,
            "liked": record.liked,
            "created_at": record.created_at,
            "session_id": record.session_id,
            "source": record.source,
        }

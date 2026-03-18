from datetime import UTC, datetime
import json
from uuid import UUID

from sqlalchemy.orm import Session

from app.auth.principal import Principal
from app.repositories.review_log_repo import ReviewLogRepository


class ReviewLogService:
    def __init__(self) -> None:
        self.review_log_repo = ReviewLogRepository()

    def create_log(
        self,
        db: Session,
        *,
        principal: Principal,
        review_input: str,
        review_result: str | None,
        raw_response: dict | list | str | None,
        normalized_result: dict | None,
        parse_status: str,
        score: int | None,
        risk_level: str | None,
        engine_source: str,
        app_mode: str | None,
        workflow_run_id: str | None,
        provider_message_id: str | None,
    ) -> dict:
        record = self.review_log_repo.create(
            db,
            user_id=UUID(principal.user_id) if principal.user_id else None,
            student_id_snapshot=principal.student_id,
            name_snapshot=principal.name,
            review_input=review_input,
            review_result=review_result,
            raw_response=self._serialize_json(raw_response),
            normalized_result=self._serialize_json(normalized_result),
            parse_status=parse_status,
            score=score,
            risk_level=risk_level,
            engine_source=engine_source,
            app_mode=app_mode,
            workflow_run_id=workflow_run_id,
            provider_message_id=provider_message_id,
            created_at=datetime.now(UTC),
        )
        db.commit()
        return self._to_payload(record)

    def list_logs(self, db: Session, *, limit: int, offset: int) -> dict:
        records = self.review_log_repo.list_all(db, limit=limit, offset=offset)
        return {"items": [self._to_payload(record) for record in records]}

    def get_log(self, db: Session, *, record_id: UUID) -> dict | None:
        record = self.review_log_repo.get_by_id(db, record_id)
        if record is None:
            return None
        return self._to_payload(record)

    @staticmethod
    def _serialize_json(value: dict | list | str | None) -> str | None:
        if value is None:
            return None
        if isinstance(value, str):
            return value
        return json.dumps(value, ensure_ascii=False)

    @staticmethod
    def _to_payload(record) -> dict:
        return {
            "id": record.id,
            "user_id": record.user_id,
            "student_id_snapshot": record.student_id_snapshot,
            "name_snapshot": record.name_snapshot,
            "review_input": record.review_input,
            "review_result": record.review_result,
            "raw_response": record.raw_response,
            "normalized_result": record.normalized_result,
            "parse_status": record.parse_status,
            "score": record.score,
            "risk_level": record.risk_level,
            "engine_source": record.engine_source,
            "app_mode": record.app_mode,
            "workflow_run_id": record.workflow_run_id,
            "provider_message_id": record.provider_message_id,
            "created_at": record.created_at,
        }


review_log_service = ReviewLogService()

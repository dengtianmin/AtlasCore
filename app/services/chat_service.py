from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy.orm import Session

from app.services.feedback_service import FeedbackService
from app.services.qa_log_service import QuestionAnswerLogService


class ChatService:
    def __init__(self) -> None:
        self.qa_log_service = QuestionAnswerLogService()
        self.feedback_service = FeedbackService()

    def ask(
        self,
        db: Session,
        *,
        question: str,
        session_id: str | None,
    ) -> dict:
        normalized_question = question.strip()
        resolved_session_id = session_id or f"session-{uuid4().hex[:12]}"
        answer = self._build_placeholder_answer(normalized_question)
        payload = self.qa_log_service.create_log(
            db,
            question=normalized_question,
            retrieved_context=None,
            answer=answer,
            session_id=resolved_session_id,
            source="atlascore",
        )
        return {
            "message_id": payload["id"],
            "session_id": resolved_session_id,
            "answer": answer,
            "source": "atlascore",
            "sources": [],
            "created_at": payload["created_at"],
        }

    def create_feedback(
        self,
        db: Session,
        *,
        message_id,
        rating: int | None,
        liked: bool | None,
        comment: str | None,
        source: str,
    ) -> dict:
        return self.feedback_service.create_feedback(
            db,
            qa_log_id=message_id,
            rating=rating,
            liked=liked,
            comment=comment,
            source=source,
        )

    def _build_placeholder_answer(self, question: str) -> str:
        timestamp = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
        return (
            "AtlasCore 已接收你的问题，并通过统一聊天入口完成记录。"
            f"\n\n当前问题：{question}"
            f"\n\n当前阶段 Dify 对话链路尚未正式接入，返回的是 AtlasCore 占位答复。"
            f"\n时间：{timestamp}"
        )

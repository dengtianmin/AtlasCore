import asyncio

from app.api.v1.chat import send_message, submit_feedback
from app.core.config import settings
from app.core.lifespan import lifespan
from app.db.session import get_session_factory, reset_db_state
from app.schemas.chat import ChatFeedbackRequest, ChatMessageRequest


async def _run_lifespan() -> None:
    from fastapi import FastAPI

    async with lifespan(FastAPI()):
        pass


def _bootstrap_runtime(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(settings, "APP_ENV", "test")
    monkeypatch.setattr(settings, "JWT_SECRET", "unit-test-secret")
    monkeypatch.setattr(settings, "SQLITE_PATH", str(tmp_path / "runtime" / "atlascore.db"))
    monkeypatch.setattr(settings, "CSV_EXPORT_DIR", str(tmp_path / "exports"))
    monkeypatch.setattr(settings, "DOCUMENT_LOCAL_STORAGE_DIR", str(tmp_path / "uploads"))
    monkeypatch.setattr(settings, "INITIAL_ADMIN_USERNAME", "admin")
    monkeypatch.setattr(settings, "INITIAL_ADMIN_PASSWORD", "StrongPass123!")
    reset_db_state()
    asyncio.run(_run_lifespan())


def test_chat_message_and_feedback_flow(monkeypatch, tmp_path):
    _bootstrap_runtime(monkeypatch, tmp_path)
    db = get_session_factory()()
    try:
        message = send_message(ChatMessageRequest(question="AtlasCore 是什么？", session_id=None), db=db)
        assert message.source == "atlascore"
        assert message.session_id.startswith("session-")
        assert "AtlasCore 已接收你的问题" in message.answer

        feedback = submit_feedback(
            message.message_id,
            ChatFeedbackRequest(rating=5, liked=True, comment="有帮助", source="web"),
            db=db,
        )
        assert feedback.qa_log_id == message.message_id
        assert feedback.liked is True
        assert feedback.rating == 5
    finally:
        db.close()

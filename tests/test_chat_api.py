import asyncio

from fastapi import HTTPException

from app.api.v1.chat import send_message, service as chat_router_service, submit_feedback
from app.core.config import settings
from app.core.lifespan import lifespan
from app.db.session import get_session_factory, reset_db_state
from app.integrations.dify.exceptions import (
    DifyConfigurationError,
    DifyServiceUnavailableError,
    DifyTimeoutError,
)
from app.schemas.chat import ChatFeedbackRequest, ChatMessageRequest
from app.services.qa_log_service import QuestionAnswerLogService


class StubDifyClient:
    def __init__(self, mode: str = "success") -> None:
        self.mode = mode

    async def run_workflow(self, *, inputs, user, response_mode, trace_id=None):
        if self.mode == "config":
            raise DifyConfigurationError("missing config")
        if self.mode == "timeout":
            raise DifyTimeoutError("timed out")
        if self.mode == "error":
            raise DifyServiceUnavailableError("upstream error")
        question = next(iter(inputs.values()))
        return type(
            "WorkflowResult",
            (),
            {
                "workflow_run_id": "run-123",
                "task_id": "task-123",
                "status": "succeeded",
                "outputs": {"text": f"Dify answer: {question}"},
                "elapsed_time": 0.5,
                "total_tokens": 42,
                "total_steps": 1,
            },
        )()


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
    monkeypatch.setattr(settings, "DIFY_TEXT_INPUT_VARIABLE", "question")
    reset_db_state()
    asyncio.run(_run_lifespan())


def test_chat_message_and_feedback_flow(monkeypatch, tmp_path):
    _bootstrap_runtime(monkeypatch, tmp_path)
    monkeypatch.setattr(chat_router_service, "dify_client", StubDifyClient(mode="success"))
    db = get_session_factory()()
    try:
        message = asyncio.run(send_message(ChatMessageRequest(question="AtlasCore 是什么？", session_id=None), db=db))
        assert message.source == "dify"
        assert message.session_id.startswith("session-")
        assert message.answer == "Dify answer: AtlasCore 是什么？"
        assert message.sources == []
        assert message.retrieved_context is None
        assert message.provider_message_id == "task-123"
        assert message.status == "succeeded"

        stored = QuestionAnswerLogService().get_log(db, record_id=message.message_id)
        assert stored is not None
        assert stored["retrieved_context"] is None
        assert stored["provider_message_id"] == "task-123"
        assert stored["status"] == "succeeded"

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


def test_chat_message_returns_controlled_error_when_dify_not_configured(monkeypatch, tmp_path):
    _bootstrap_runtime(monkeypatch, tmp_path)
    monkeypatch.setattr(chat_router_service, "dify_client", StubDifyClient(mode="config"))
    db = get_session_factory()()
    try:
        try:
            asyncio.run(send_message(ChatMessageRequest(question="配置缺失怎么办？", session_id="session-a"), db=db))
        except HTTPException as exc:
            assert exc.status_code == 503
            assert exc.detail == "Chat integration is not configured"
        else:
            raise AssertionError("Expected controlled 503 when Dify config is missing")

        items = QuestionAnswerLogService().list_logs(db, limit=10, offset=0)["items"]
        assert items[0]["status"] == "failed"
        assert items[0]["error_code"] == "dify_not_configured"
    finally:
        db.close()


def test_chat_message_returns_controlled_error_when_dify_times_out(monkeypatch, tmp_path):
    _bootstrap_runtime(monkeypatch, tmp_path)
    monkeypatch.setattr(chat_router_service, "dify_client", StubDifyClient(mode="timeout"))
    db = get_session_factory()()
    try:
        try:
            asyncio.run(send_message(ChatMessageRequest(question="超时测试", session_id="session-b"), db=db))
        except HTTPException as exc:
            assert exc.status_code == 504
            assert exc.detail == "Chat provider timed out"
        else:
            raise AssertionError("Expected controlled 504 when Dify times out")
    finally:
        db.close()


def test_chat_message_returns_controlled_error_when_dify_fails(monkeypatch, tmp_path):
    _bootstrap_runtime(monkeypatch, tmp_path)
    monkeypatch.setattr(chat_router_service, "dify_client", StubDifyClient(mode="error"))
    db = get_session_factory()()
    try:
        try:
            asyncio.run(send_message(ChatMessageRequest(question="失败测试", session_id="session-c"), db=db))
        except HTTPException as exc:
            assert exc.status_code == 502
            assert exc.detail == "Chat provider request failed"
        else:
            raise AssertionError("Expected controlled 502 when Dify request fails")
    finally:
        db.close()

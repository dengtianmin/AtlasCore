import asyncio

from app.api.v1.chat import service as chat_router_service
from app.api.v1.admin_logs import get_log, list_logs
from app.api.v1.chat import send_message, submit_feedback
from app.auth.principal import Principal
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


def _admin() -> Principal:
    return Principal(user_id="00000000-0000-0000-0000-000000000001", username="admin", roles=["admin"])


class StubDifyClient:
    async def run_workflow(self, *, inputs, user, response_mode, trace_id=None):
        question = next(iter(inputs.values()))
        return type(
            "WorkflowResult",
            (),
            {
                "workflow_run_id": "run-1",
                "task_id": "task-1",
                "status": "succeeded",
                "outputs": {"text": f"Answer: {question}"},
                "elapsed_time": 0.5,
                "total_tokens": 10,
                "total_steps": 1,
            },
        )()


def test_admin_logs_list_and_detail(monkeypatch, tmp_path):
    _bootstrap_runtime(monkeypatch, tmp_path)
    monkeypatch.setattr(settings, "DIFY_TEXT_INPUT_VARIABLE", "question")
    monkeypatch.setattr(chat_router_service, "dify_client", StubDifyClient())
    db = get_session_factory()()
    try:
        first = asyncio.run(send_message(ChatMessageRequest(question="AtlasCore 是什么？", session_id="s-1"), db=db))
        second = asyncio.run(send_message(ChatMessageRequest(question="图谱接口做什么？", session_id="s-2"), db=db))
        submit_feedback(
            first.message_id,
            ChatFeedbackRequest(rating=4, liked=True, comment="不错", source="web"),
            db=db,
        )

        listed = list_logs(
            _=_admin(),
            db=db,
            limit=50,
            offset=0,
            keyword="AtlasCore",
            source=None,
            liked=True,
            rating=None,
            date_from=None,
            date_to=None,
        )
        assert len(listed.items) == 1
        assert listed.items[0].id == first.message_id
        assert listed.items[0].feedback is not None
        assert listed.items[0].feedback.liked is True
        assert listed.items[0].feedback_count == 1

        detail = get_log(first.message_id, _=_admin(), db=db)
        assert detail.id == first.message_id
        assert detail.feedback is not None
        assert detail.feedback_count == 1

        no_match = list_logs(
            _=_admin(),
            db=db,
            limit=50,
            offset=0,
            keyword=None,
            source="atlascore",
            liked=None,
            rating=5,
            date_from=None,
            date_to=None,
        )
        assert no_match.items == []

        all_logs = list_logs(
            _=_admin(),
            db=db,
            limit=50,
            offset=0,
            keyword=None,
            source=None,
            liked=None,
            rating=None,
            date_from=None,
            date_to=None,
        )
        assert len(all_logs.items) == 2
        assert all_logs.items[0].id in {first.message_id, second.message_id}
    finally:
        db.close()

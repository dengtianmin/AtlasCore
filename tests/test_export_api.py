import asyncio
from pathlib import Path

from fastapi import HTTPException

from app.api.v1.admin_exports import download_export, export_feedback, export_qa_logs, list_exports
from app.api.v1.root import root
from app.api.v1.chat import send_message, service as chat_router_service, submit_feedback
from app.auth.principal import Principal
from app.core.config import settings
from app.core.lifespan import lifespan
from app.db.session import get_session_factory, reset_db_state
from app.schemas.admin import ExportTriggerRequest
from app.schemas.chat import ChatFeedbackRequest, ChatMessageRequest
from app.services.runtime_status_service import runtime_status_service


async def _run_lifespan() -> None:
    from fastapi import FastAPI

    async with lifespan(FastAPI()):
        pass


def _bootstrap_runtime(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(settings, "APP_ENV", "test")
    monkeypatch.setattr(settings, "JWT_SECRET", "unit-test-secret")
    monkeypatch.setattr(settings, "DIFY_BASE_URL", None)
    monkeypatch.setattr(settings, "DIFY_API_KEY", None)
    monkeypatch.setattr(settings, "DIFY_API_KEY_SECRET_NAME", None)
    monkeypatch.setattr(settings, "SQLITE_PATH", str(tmp_path / "runtime" / "atlascore.db"))
    monkeypatch.setattr(settings, "CSV_EXPORT_DIR", str(tmp_path / "exports"))
    monkeypatch.setattr(settings, "DOCUMENT_LOCAL_STORAGE_DIR", str(tmp_path / "uploads"))
    monkeypatch.setattr(settings, "INITIAL_ADMIN_USERNAME", "admin")
    monkeypatch.setattr(settings, "INITIAL_ADMIN_PASSWORD", "StrongPass123!")
    reset_db_state()
    runtime_status_service.reset()
    asyncio.run(_run_lifespan())


def _admin_principal() -> Principal:
    return Principal(user_id="00000000-0000-0000-0000-000000000001", username="admin", roles=["admin"])


def _user_principal() -> Principal:
    return Principal(
        user_id="11111111-1111-1111-1111-111111111111",
        username="2025000001",
        student_id="2025000001",
        name="张三",
        roles=["user"],
        role="user",
        scope="user",
        token_type="user_access",
    )


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


def test_root_and_export_api_flow(monkeypatch, tmp_path):
    _bootstrap_runtime(monkeypatch, tmp_path)
    db = get_session_factory()()
    try:
        monkeypatch.setattr(settings, "DIFY_TEXT_INPUT_VARIABLE", "question")
        monkeypatch.setattr(chat_router_service, "dify_client", StubDifyClient())
        asyncio.run(
            send_message(
                ChatMessageRequest(question="What is AtlasCore?", session_id="session-1"),
                principal=_user_principal(),
                db=db,
            )
        )

        root_before = root(db=db)
        assert root_before["health_url"] == "/health"
        assert root_before["latest_export"] is None

        export_payload = export_qa_logs(
            ExportTriggerRequest(operator="root-admin"),
            _=_admin_principal(),
        )
        assert export_payload.success is True
        assert export_payload.record_count == 1
        assert export_payload.download_url.startswith("/api/admin/exports/download/")

        list_payload = list_exports(_=_admin_principal())
        assert len(list_payload.items) == 1
        assert list_payload.items[0].filename == export_payload.filename

        response = download_export(export_payload.filename, _=_admin_principal())
        assert response.media_type == "text/csv"
        assert Path(response.path).exists()
        content = Path(response.path).read_text(encoding="utf-8")
        assert "What is AtlasCore?" in content
        assert "2025000001" in content
        assert "张三" in content
        status = asyncio.run(runtime_status_service.get_status())
        assert status["last_csv_export"]["filename"] == export_payload.filename
        assert status["last_csv_export"]["status"] == "success"

        root_after = root(db=db)
        assert root_after["latest_export"]["filename"] == export_payload.filename
    finally:
        db.close()


def test_feedback_export_api_flow(monkeypatch, tmp_path):
    _bootstrap_runtime(monkeypatch, tmp_path)
    db = get_session_factory()()
    try:
        monkeypatch.setattr(settings, "DIFY_TEXT_INPUT_VARIABLE", "question")
        monkeypatch.setattr(chat_router_service, "dify_client", StubDifyClient())
        log = asyncio.run(
            send_message(
                ChatMessageRequest(question="What is AtlasCore?", session_id="session-1"),
                principal=_user_principal(),
                db=db,
            )
        )
        submit_feedback(
            log.message_id,
            payload=ChatFeedbackRequest(rating=5, liked=True, comment="good", source="web"),
            _=_user_principal(),
            db=db,
        )

        export_payload = export_feedback(
            ExportTriggerRequest(operator="root-admin"),
            _=_admin_principal(),
        )
        assert export_payload.success is True
        assert export_payload.record_count == 1
        assert export_payload.filename.startswith("feedback_")

        response = download_export(export_payload.filename, _=_admin_principal())
        assert response.media_type == "text/csv"
        content = Path(response.path).read_text(encoding="utf-8")
        assert "qa_log_id" in content
        assert "good" in content
        assert "2025000001" in content
        assert "张三" in content
    finally:
        db.close()


def test_export_download_rejects_path_traversal(monkeypatch, tmp_path):
    _bootstrap_runtime(monkeypatch, tmp_path)

    try:
        download_export("../secret.csv", _=_admin_principal())
    except HTTPException as exc:
        assert exc.status_code == 400
        assert exc.detail == "Invalid export filename"
    else:
        raise AssertionError("Expected download_export to reject path traversal input")

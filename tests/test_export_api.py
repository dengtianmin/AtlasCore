import asyncio
from pathlib import Path

from fastapi import HTTPException

from app.api.v1.admin_exports import download_export, export_qa_logs, list_exports
from app.api.v1.debug import create_qa_log
from app.api.v1.root import root
from app.auth.principal import Principal
from app.core.config import settings
from app.core.lifespan import lifespan
from app.db.session import get_session_factory, reset_db_state
from app.schemas.admin import ExportTriggerRequest
from app.schemas.debug import QuestionAnswerLogCreateRequest
from app.services.runtime_status_service import runtime_status_service


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
    runtime_status_service.reset()
    asyncio.run(_run_lifespan())


def _admin_principal() -> Principal:
    return Principal(user_id="00000000-0000-0000-0000-000000000001", username="admin", roles=["admin"])


def test_root_and_export_api_flow(monkeypatch, tmp_path):
    _bootstrap_runtime(monkeypatch, tmp_path)
    db = get_session_factory()()
    try:
        create_qa_log(
            QuestionAnswerLogCreateRequest(
                question="What is AtlasCore?",
                retrieved_context="AtlasCore is the Azure backend layer.",
                answer="AtlasCore handles system-level backend capabilities.",
                session_id="session-1",
                source="dify",
            ),
            db=db,
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
        assert "What is AtlasCore?" in Path(response.path).read_text(encoding="utf-8")
        status = runtime_status_service.get_status()
        assert status["last_csv_export"]["filename"] == export_payload.filename
        assert status["last_csv_export"]["status"] == "success"

        root_after = root(db=db)
        assert root_after["latest_export"]["filename"] == export_payload.filename
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

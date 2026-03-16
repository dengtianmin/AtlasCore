import asyncio
from pathlib import Path

from fastapi import FastAPI

from app.api.v1.debug import create_qa_log, export_qa_logs, get_qa_log, list_qa_logs
from app.core.config import settings
from app.core.lifespan import lifespan
from app.db.session import get_session_factory, reset_db_state
from app.schemas.debug import ExportRequest, QuestionAnswerLogCreateRequest
from app.services.auth_service import AuthService


async def _run_lifespan() -> None:
    async with lifespan(FastAPI()):
        pass


def test_debug_qa_log_flow(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "SQLITE_PATH", str(tmp_path / "runtime" / "atlascore.db"))
    monkeypatch.setattr(settings, "CSV_EXPORT_DIR", str(tmp_path / "exports"))
    monkeypatch.setattr(settings, "DOCUMENT_LOCAL_STORAGE_DIR", str(tmp_path / "uploads"))
    monkeypatch.setattr(settings, "INITIAL_ADMIN_USERNAME", "admin")
    monkeypatch.setattr(settings, "INITIAL_ADMIN_PASSWORD", "StrongPass123!")
    reset_db_state()
    asyncio.run(_run_lifespan())

    db = get_session_factory()()
    try:
        created = create_qa_log(
            QuestionAnswerLogCreateRequest(
                question="What is AtlasCore?",
                retrieved_context="AtlasCore is an Azure backend.",
                answer="AtlasCore is the Azure backend layer.",
                rating=5,
                liked=True,
                session_id="session-1",
                source="dify",
            ),
            db=db,
        )
        listed = list_qa_logs(db=db, limit=50, offset=0)
        fetched = get_qa_log(record_id=created.id, db=db)
        exported = export_qa_logs(ExportRequest(operator="debug-admin"), db=db)
    finally:
        db.close()

    assert created.question == "What is AtlasCore?"
    assert len(listed.items) == 1
    assert fetched.id == created.id
    assert exported.record_count == 1
    assert exported.operator == "debug-admin"
    assert Path(exported.file_path).exists()


def test_lifespan_bootstraps_admin_account(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "SQLITE_PATH", str(tmp_path / "runtime" / "atlascore.db"))
    monkeypatch.setattr(settings, "CSV_EXPORT_DIR", str(tmp_path / "exports"))
    monkeypatch.setattr(settings, "DOCUMENT_LOCAL_STORAGE_DIR", str(tmp_path / "uploads"))
    monkeypatch.setattr(settings, "INITIAL_ADMIN_USERNAME", "bootstrap-admin")
    monkeypatch.setattr(settings, "INITIAL_ADMIN_PASSWORD", "StrongPass123!")
    reset_db_state()
    asyncio.run(_run_lifespan())

    db = get_session_factory()()
    try:
        response = AuthService().login(db, username="bootstrap-admin", password="StrongPass123!")
    finally:
        db.close()

    assert response.token_type == "bearer"

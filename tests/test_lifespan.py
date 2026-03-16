import asyncio
from pathlib import Path

from fastapi import FastAPI
from sqlalchemy import inspect

from app.core.config import settings
from app.core.lifespan import lifespan
from app.db.session import reset_db_state
from app.graph.db import get_graph_engine, reset_graph_db_state
from app.services.runtime_status_service import runtime_status_service


async def _run_lifespan(app: FastAPI) -> None:
    async with lifespan(app):
        pass


def test_lifespan_context_runs_without_error(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "SQLITE_PATH", str(tmp_path / "runtime" / "atlascore.db"))
    monkeypatch.setattr(settings, "CSV_EXPORT_DIR", str(tmp_path / "exports"))
    monkeypatch.setattr(settings, "DOCUMENT_LOCAL_STORAGE_DIR", str(tmp_path / "uploads"))
    monkeypatch.setattr(settings, "GRAPH_EXPORT_DIR", str(tmp_path / "graph_exports"))
    monkeypatch.setattr(settings, "GRAPH_IMPORT_DIR", str(tmp_path / "graph_imports"))
    monkeypatch.setattr(settings, "GRAPH_INSTANCE_LOCAL_PATH", str(tmp_path / "graph" / "atlascore_graph.db"))
    monkeypatch.setattr(settings, "GRAPH_INSTANCE_ID", "test-instance")
    monkeypatch.setattr(settings, "GRAPH_ENABLED", True)
    monkeypatch.setattr(settings, "GRAPH_RELOAD_ON_START", True)
    reset_db_state()
    reset_graph_db_state()
    runtime_status_service.reset()

    app = FastAPI()
    asyncio.run(_run_lifespan(app))

    assert Path(settings.SQLITE_PATH).exists()
    assert Path(settings.CSV_EXPORT_DIR).is_dir()
    assert Path(settings.DOCUMENT_LOCAL_STORAGE_DIR).is_dir()
    assert Path(settings.GRAPH_EXPORT_DIR).is_dir()
    assert Path(settings.GRAPH_IMPORT_DIR).is_dir()
    assert Path(settings.graph_instance_path).exists()

    inspector = inspect(get_graph_engine())
    assert {"graph_nodes", "graph_edges", "graph_sync_records", "graph_versions"}.issubset(
        set(inspector.get_table_names())
    )

    status = runtime_status_service.get_status()
    assert status["config_loaded"] is True
    assert status["sqlite_ready"] is True
    assert status["migration_ready"] is True
    assert status["graph_enabled"] is True

import asyncio
from pathlib import Path

from fastapi import FastAPI

from app.core.config import settings
from app.core.lifespan import lifespan
from app.db.session import reset_db_state


async def _run_lifespan(app: FastAPI) -> None:
    async with lifespan(app):
        pass


def test_lifespan_context_runs_without_error(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "SQLITE_PATH", str(tmp_path / "runtime" / "atlascore.db"))
    monkeypatch.setattr(settings, "CSV_EXPORT_DIR", str(tmp_path / "exports"))
    monkeypatch.setattr(settings, "DOCUMENT_LOCAL_STORAGE_DIR", str(tmp_path / "uploads"))
    reset_db_state()

    app = FastAPI()
    asyncio.run(_run_lifespan(app))

    assert Path(settings.SQLITE_PATH).exists()
    assert Path(settings.CSV_EXPORT_DIR).is_dir()
    assert Path(settings.DOCUMENT_LOCAL_STORAGE_DIR).is_dir()

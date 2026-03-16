from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

from app.core.config import settings
from app.db.session import initialize_database

@asynccontextmanager
async def lifespan(_: FastAPI):
    Path(settings.CSV_EXPORT_DIR).expanduser().mkdir(parents=True, exist_ok=True)
    Path(settings.DOCUMENT_LOCAL_STORAGE_DIR).expanduser().mkdir(parents=True, exist_ok=True)
    initialize_database()
    yield

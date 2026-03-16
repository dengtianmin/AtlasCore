from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

from app.core.config import settings
from app.db.session import initialize_database
from app.db.session import get_session_factory
from app.graph.db import initialize_graph_database
from app.services.auth_service import AuthService

@asynccontextmanager
async def lifespan(_: FastAPI):
    Path(settings.CSV_EXPORT_DIR).expanduser().mkdir(parents=True, exist_ok=True)
    Path(settings.DOCUMENT_LOCAL_STORAGE_DIR).expanduser().mkdir(parents=True, exist_ok=True)
    Path(settings.GRAPH_EXPORT_DIR).expanduser().mkdir(parents=True, exist_ok=True)
    Path(settings.GRAPH_IMPORT_DIR).expanduser().mkdir(parents=True, exist_ok=True)
    initialize_database()
    if settings.GRAPH_ENABLED:
        initialize_graph_database()
    admin_password = settings.resolved_initial_admin_password
    if settings.INITIAL_ADMIN_USERNAME and admin_password:
        session = get_session_factory()()
        try:
            AuthService().ensure_admin_account(
                session,
                username=settings.INITIAL_ADMIN_USERNAME,
                password=admin_password,
            )
        finally:
            session.close()
    yield

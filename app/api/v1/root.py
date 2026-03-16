from collections.abc import Generator
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db_session
from app.services.csv_export_service import CsvExportService

router = APIRouter(tags=["root"])
export_service = CsvExportService()


def get_session() -> Generator[Session, None, None]:
    yield from get_db_session()


@router.get("/")
def root(
    db: Annotated[Session, Depends(get_session)],
) -> dict:
    latest_export = export_service.get_latest_export(db)
    return {
        "service": settings.APP_NAME,
        "status": "ok",
        "health_url": "/health",
        "exports_api": {
            "trigger_qa_logs": "/api/admin/exports/qa-logs",
            "list": "/api/admin/exports",
        },
        "latest_export": latest_export,
    }

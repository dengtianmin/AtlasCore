from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.auth.dependencies import require_roles
from app.auth.principal import Principal
from app.auth.rbac import ROLE_ADMIN
from app.db.session import get_db_session
from app.schemas.admin import (
    ExportListResponse,
    ExportRecordResponse,
    ExportTriggerRequest,
    ExportTriggerResponse,
)
from app.services.csv_export_service import CsvExportService

router = APIRouter(prefix="/api/admin/exports", tags=["admin-exports"])
export_service = CsvExportService()


def _db_dependency() -> Session:
    try:
        session_gen = get_db_session()
        return next(session_gen)
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is not configured",
        ) from exc


@router.post("/qa-logs", response_model=ExportTriggerResponse)
def export_qa_logs(
    payload: ExportTriggerRequest,
    _: Annotated[Principal, Depends(require_roles(ROLE_ADMIN))],
) -> ExportTriggerResponse:
    db = _db_dependency()
    try:
        result = export_service.export_qa_logs(db, operator=payload.operator)
        return ExportTriggerResponse(**result)
    finally:
        db.close()


@router.post("/feedback", response_model=ExportTriggerResponse)
def export_feedback(
    payload: ExportTriggerRequest,
    _: Annotated[Principal, Depends(require_roles(ROLE_ADMIN))],
) -> ExportTriggerResponse:
    db = _db_dependency()
    try:
        result = export_service.export_feedback(db, operator=payload.operator)
        return ExportTriggerResponse(**result)
    finally:
        db.close()


@router.get("", response_model=ExportListResponse)
def list_exports(
    _: Annotated[Principal, Depends(require_roles(ROLE_ADMIN))],
) -> ExportListResponse:
    db = _db_dependency()
    try:
        result = export_service.list_exports(db)
        return ExportListResponse(**result)
    finally:
        db.close()


@router.get("/latest", response_model=ExportRecordResponse)
def latest_export(
    _: Annotated[Principal, Depends(require_roles(ROLE_ADMIN))],
) -> ExportRecordResponse:
    db = _db_dependency()
    try:
        result = export_service.get_latest_export(db)
        if result is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No exports available")
        return ExportRecordResponse(**result)
    finally:
        db.close()


@router.get("/download/{filename}")
def download_export(
    filename: str,
    _: Annotated[Principal, Depends(require_roles(ROLE_ADMIN))],
) -> FileResponse:
    file_path = export_service.resolve_download_path(filename)
    return FileResponse(path=file_path, media_type="text/csv", filename=file_path.name)

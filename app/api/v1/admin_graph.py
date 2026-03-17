from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.auth.dependencies import require_roles
from app.auth.principal import Principal
from app.auth.rbac import ROLE_ADMIN
from app.db.session import get_db_session
from app.schemas.admin import GraphAdminStatusResponse, GraphClearResponse, GraphFileOperationResponse, GraphReloadResponse
from app.services.graph_service import GraphService

router = APIRouter(prefix="/api/admin/graph", tags=["admin-graph"])
service = GraphService()


def _db_dependency() -> Session:
    try:
        session_gen = get_db_session()
        return next(session_gen)
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database is not configured") from exc


@router.get("/status", response_model=GraphAdminStatusResponse)
def graph_status(
    _: Annotated[Principal, Depends(require_roles(ROLE_ADMIN))],
) -> GraphAdminStatusResponse:
    return GraphAdminStatusResponse(**service.get_admin_status())


@router.post("/reload", response_model=GraphReloadResponse)
def reload_graph(
    _: Annotated[Principal, Depends(require_roles(ROLE_ADMIN))],
) -> GraphReloadResponse:
    return GraphReloadResponse(**service.reload_graph())


@router.post("/export", response_model=GraphFileOperationResponse)
def export_graph(
    _: Annotated[Principal, Depends(require_roles(ROLE_ADMIN))],
) -> GraphFileOperationResponse:
    return GraphFileOperationResponse(**service.export_graph_sqlite())


@router.post("/import", response_model=GraphFileOperationResponse)
def import_graph(
    _: Annotated[Principal, Depends(require_roles(ROLE_ADMIN))],
    file: UploadFile = File(...),
) -> GraphFileOperationResponse:
    return GraphFileOperationResponse(**service.import_graph_sqlite(file))


@router.get("/download/{filename}")
def download_graph_export(
    filename: str,
    _: Annotated[Principal, Depends(require_roles(ROLE_ADMIN))],
) -> FileResponse:
    file_path = service.resolve_export_download_path(filename)
    return FileResponse(path=file_path, media_type="application/x-sqlite3", filename=file_path.name)


@router.post("/clear", response_model=GraphClearResponse)
def clear_graph(
    current_admin: Annotated[Principal, Depends(require_roles(ROLE_ADMIN))],
) -> GraphClearResponse:
    db = _db_dependency()
    try:
        return GraphClearResponse(**service.clear_graph(db, operator=current_admin.username))
    finally:
        db.close()

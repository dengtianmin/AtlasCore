from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.auth.dependencies import require_roles
from app.auth.principal import Principal
from app.auth.rbac import ROLE_ADMIN
from app.db.session import get_db_session
from app.schemas.admin import (
    ExtractionTaskCreateRequest,
    ExtractionTaskListResponse,
    ExtractionTaskResponse,
    GraphFileListResponse,
    GraphModelSettingResponse,
    GraphModelSettingUpdateRequest,
    GraphPromptSettingResponse,
    GraphPromptSettingUpdateRequest,
    GraphSqliteActivateResponse,
)
from app.services.graph_extraction_service import graph_extraction_service

router = APIRouter(prefix="/api/admin/graph", tags=["admin-graph-extraction"])


def _db_dependency() -> Session:
    try:
        session_gen = get_db_session()
        return next(session_gen)
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database is not configured") from exc


@router.get("/sqlite-files", response_model=GraphFileListResponse)
def list_sqlite_files(
    _: Annotated[Principal, Depends(require_roles(ROLE_ADMIN))],
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> GraphFileListResponse:
    db = _db_dependency()
    try:
        return GraphFileListResponse(**graph_extraction_service.list_files(db, file_type="sqlite", limit=limit, offset=offset))
    finally:
        db.close()


@router.post("/sqlite-files/upload", response_model=ExtractionTaskResponse, status_code=status.HTTP_201_CREATED)
def upload_sqlite_file(
    current_admin: Annotated[Principal, Depends(require_roles(ROLE_ADMIN))],
    file: UploadFile = File(...),
) -> ExtractionTaskResponse:
    db = _db_dependency()
    try:
        payload = graph_extraction_service.upload_file(
            db,
            upload=file,
            admin_user_id=UUID(current_admin.user_id),
            file_type="sqlite",
        )
        return ExtractionTaskResponse.model_validate(payload)
    finally:
        db.close()


@router.post("/sqlite-files/{document_id}/activate", response_model=GraphSqliteActivateResponse)
def activate_sqlite_file(
    document_id: UUID,
    current_admin: Annotated[Principal, Depends(require_roles(ROLE_ADMIN))],
) -> GraphSqliteActivateResponse:
    db = _db_dependency()
    try:
        payload = graph_extraction_service.activate_sqlite_file(db, document_id=document_id, operator=current_admin.username)
        return GraphSqliteActivateResponse(**payload)
    finally:
        db.close()


@router.get("/md-files", response_model=GraphFileListResponse)
def list_md_files(
    _: Annotated[Principal, Depends(require_roles(ROLE_ADMIN))],
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> GraphFileListResponse:
    db = _db_dependency()
    try:
        return GraphFileListResponse(**graph_extraction_service.list_files(db, file_type="md", limit=limit, offset=offset))
    finally:
        db.close()


@router.post("/md-files/upload", response_model=ExtractionTaskResponse, status_code=status.HTTP_201_CREATED)
def upload_md_file(
    current_admin: Annotated[Principal, Depends(require_roles(ROLE_ADMIN))],
    file: UploadFile = File(...),
) -> ExtractionTaskResponse:
    db = _db_dependency()
    try:
        payload = graph_extraction_service.upload_file(
            db,
            upload=file,
            admin_user_id=UUID(current_admin.user_id),
            file_type="md",
        )
        return ExtractionTaskResponse.model_validate(payload)
    finally:
        db.close()


@router.delete("/md-files/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_md_file(
    document_id: UUID,
    _: Annotated[Principal, Depends(require_roles(ROLE_ADMIN))],
) -> None:
    db = _db_dependency()
    try:
        graph_extraction_service.delete_md_file(db, document_id=document_id)
    finally:
        db.close()


@router.post("/extraction-tasks", response_model=ExtractionTaskResponse, status_code=status.HTTP_201_CREATED)
async def create_extraction_task(
    payload: ExtractionTaskCreateRequest,
    current_admin: Annotated[Principal, Depends(require_roles(ROLE_ADMIN))],
) -> ExtractionTaskResponse:
    db = _db_dependency()
    try:
        result = await graph_extraction_service.create_extraction_task(
            db,
            document_ids=payload.document_ids,
            operator=current_admin.username,
        )
        return ExtractionTaskResponse(**result)
    finally:
        db.close()


@router.get("/extraction-tasks", response_model=ExtractionTaskListResponse)
def list_extraction_tasks(
    _: Annotated[Principal, Depends(require_roles(ROLE_ADMIN))],
    limit: int = Query(default=20, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> ExtractionTaskListResponse:
    db = _db_dependency()
    try:
        return ExtractionTaskListResponse(**graph_extraction_service.list_tasks(db, limit=limit, offset=offset))
    finally:
        db.close()


@router.get("/extraction-tasks/{task_id}", response_model=ExtractionTaskResponse)
def get_extraction_task(
    task_id: UUID,
    _: Annotated[Principal, Depends(require_roles(ROLE_ADMIN))],
) -> ExtractionTaskResponse:
    db = _db_dependency()
    try:
        return ExtractionTaskResponse(**graph_extraction_service.get_task(db, task_id=task_id))
    finally:
        db.close()


@router.get("/prompt-settings", response_model=GraphPromptSettingResponse)
def get_prompt_settings(
    _: Annotated[Principal, Depends(require_roles(ROLE_ADMIN))],
) -> GraphPromptSettingResponse:
    db = _db_dependency()
    try:
        return GraphPromptSettingResponse(**graph_extraction_service.get_prompt_setting(db))
    finally:
        db.close()


@router.put("/prompt-settings", response_model=GraphPromptSettingResponse)
def update_prompt_settings(
    payload: GraphPromptSettingUpdateRequest,
    current_admin: Annotated[Principal, Depends(require_roles(ROLE_ADMIN))],
) -> GraphPromptSettingResponse:
    db = _db_dependency()
    try:
        return GraphPromptSettingResponse(
            **graph_extraction_service.update_prompt_setting(db, prompt_text=payload.prompt_text, operator=current_admin.username)
        )
    finally:
        db.close()


@router.get("/model-settings", response_model=GraphModelSettingResponse)
def get_model_settings(
    _: Annotated[Principal, Depends(require_roles(ROLE_ADMIN))],
) -> GraphModelSettingResponse:
    db = _db_dependency()
    try:
        return GraphModelSettingResponse(**graph_extraction_service.get_model_setting(db))
    finally:
        db.close()


@router.put("/model-settings", response_model=GraphModelSettingResponse)
def update_model_settings(
    payload: GraphModelSettingUpdateRequest,
    current_admin: Annotated[Principal, Depends(require_roles(ROLE_ADMIN))],
) -> GraphModelSettingResponse:
    db = _db_dependency()
    try:
        return GraphModelSettingResponse(
            **graph_extraction_service.update_model_setting(
                db,
                provider=payload.provider,
                model_name=payload.model_name,
                api_base_url=payload.api_base_url,
                api_key=payload.api_key,
                enabled=payload.enabled,
                operator=current_admin.username,
            )
        )
    finally:
        db.close()

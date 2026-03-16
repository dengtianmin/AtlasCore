from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.auth.dependencies import require_roles
from app.auth.principal import Principal
from app.auth.rbac import ROLE_ADMIN
from app.db.session import get_db_session
from app.schemas.admin import (
    DocumentListResponse,
    DocumentStatusResponse,
    DocumentUploadResponse,
    SyncTriggerResponse,
)
from app.services.admin_service import AdminDocumentService

router = APIRouter(prefix="/admin", tags=["admin"])
service = AdminDocumentService()


def _db_dependency() -> Session:
    try:
        session_gen = get_db_session()
        return next(session_gen)
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is not configured",
        ) from exc


@router.get("/ping")
def admin_ping(
    _: Annotated[Principal, Depends(require_roles(ROLE_ADMIN))],
) -> dict[str, str]:
    return {"status": "ok", "scope": "admin"}


@router.post("/documents/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
def upload_document(
    current_admin: Annotated[Principal, Depends(require_roles(ROLE_ADMIN))],
    file: UploadFile = File(...),
) -> DocumentUploadResponse:
    db = _db_dependency()
    try:
        payload = service.upload_document(db, upload=file, admin_user_id=UUID(current_admin.user_id))
        return DocumentUploadResponse(**payload)
    finally:
        db.close()


@router.get("/documents", response_model=DocumentListResponse)
def list_documents(
    _: Annotated[Principal, Depends(require_roles(ROLE_ADMIN))],
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> DocumentListResponse:
    db = _db_dependency()
    try:
        payload = service.list_documents(db, limit=limit, offset=offset)
        return DocumentListResponse(**payload)
    finally:
        db.close()


@router.get("/documents/{document_id}", response_model=DocumentUploadResponse)
def get_document(
    document_id: UUID,
    _: Annotated[Principal, Depends(require_roles(ROLE_ADMIN))],
) -> DocumentUploadResponse:
    db = _db_dependency()
    try:
        payload = service.get_document(db, doc_id=document_id)
        return DocumentUploadResponse(**payload)
    finally:
        db.close()


@router.get("/documents/{document_id}/status", response_model=DocumentStatusResponse)
def get_document_status(
    document_id: UUID,
    _: Annotated[Principal, Depends(require_roles(ROLE_ADMIN))],
) -> DocumentStatusResponse:
    db = _db_dependency()
    try:
        payload = service.get_document(db, doc_id=document_id)
        return DocumentStatusResponse(id=payload["id"], status=payload["status"], uploaded_at=payload["uploaded_at"])
    finally:
        db.close()


@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: UUID,
    _: Annotated[Principal, Depends(require_roles(ROLE_ADMIN))],
) -> None:
    db = _db_dependency()
    try:
        service.delete_document(db, doc_id=document_id)
    finally:
        db.close()


@router.post("/documents/{document_id}/graph-sync", response_model=SyncTriggerResponse)
def trigger_graph_sync(
    document_id: UUID,
    _: Annotated[Principal, Depends(require_roles(ROLE_ADMIN))],
) -> SyncTriggerResponse:
    db = _db_dependency()
    try:
        payload = service.trigger_graph_sync(db, doc_id=document_id)
        return SyncTriggerResponse(**payload)
    finally:
        db.close()


@router.post("/documents/{document_id}/dify-sync", response_model=SyncTriggerResponse)
def trigger_dify_sync(
    document_id: UUID,
    _: Annotated[Principal, Depends(require_roles(ROLE_ADMIN))],
) -> SyncTriggerResponse:
    db = _db_dependency()
    try:
        payload = service.trigger_dify_index(db, doc_id=document_id)
        return SyncTriggerResponse(**payload)
    finally:
        db.close()

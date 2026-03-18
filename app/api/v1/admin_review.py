from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth.dependencies import require_roles
from app.auth.principal import Principal
from app.auth.rbac import ROLE_ADMIN
from app.db.session import get_db_session
from app.schemas.review import (
    ReviewDifyConfigSummaryResponse,
    ReviewDifyConfigUpdateRequest,
    ReviewLogListResponse,
    ReviewLogRecordResponse,
    ReviewRubricResponse,
    ReviewRubricUpdateRequest,
)
from app.services.review_log_service import review_log_service
from app.services.review_service import review_service

router = APIRouter(prefix="/api/admin/review", tags=["admin-review"])


def _db_dependency() -> Session:
    try:
        session_gen = get_db_session()
        return next(session_gen)
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database is not configured") from exc


@router.get("/rubric", response_model=ReviewRubricResponse)
def get_review_rubric(
    _: Annotated[Principal, Depends(require_roles(ROLE_ADMIN))],
) -> ReviewRubricResponse:
    db = _db_dependency()
    try:
        return ReviewRubricResponse(**review_service.get_rubric(db))
    finally:
        db.close()


@router.put("/rubric", response_model=ReviewRubricResponse)
def update_review_rubric(
    payload: ReviewRubricUpdateRequest,
    current_admin: Annotated[Principal, Depends(require_roles(ROLE_ADMIN))],
) -> ReviewRubricResponse:
    db = _db_dependency()
    try:
        return ReviewRubricResponse(**review_service.update_rubric(db, rubric_text=payload.rubric_text, operator=current_admin.username))
    finally:
        db.close()


@router.get("/config", response_model=ReviewDifyConfigSummaryResponse)
def get_review_dify_config(
    _: Annotated[Principal, Depends(require_roles(ROLE_ADMIN))],
) -> ReviewDifyConfigSummaryResponse:
    db = _db_dependency()
    try:
        return ReviewDifyConfigSummaryResponse(**review_service.get_review_dify_config(db))
    finally:
        db.close()


@router.put("/config", response_model=ReviewDifyConfigSummaryResponse)
def update_review_dify_config(
    payload: ReviewDifyConfigUpdateRequest,
    current_admin: Annotated[Principal, Depends(require_roles(ROLE_ADMIN))],
) -> ReviewDifyConfigSummaryResponse:
    db = _db_dependency()
    try:
        return ReviewDifyConfigSummaryResponse(
            **review_service.update_review_dify_config(db, payload=payload.model_dump(), operator=current_admin.username)
        )
    finally:
        db.close()


@router.get("/logs", response_model=ReviewLogListResponse)
def list_review_logs(
    _: Annotated[Principal, Depends(require_roles(ROLE_ADMIN))],
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> ReviewLogListResponse:
    db = _db_dependency()
    try:
        return ReviewLogListResponse(**review_log_service.list_logs(db, limit=limit, offset=offset))
    finally:
        db.close()


@router.get("/logs/{record_id}", response_model=ReviewLogRecordResponse)
def get_review_log(
    record_id: UUID,
    _: Annotated[Principal, Depends(require_roles(ROLE_ADMIN))],
) -> ReviewLogRecordResponse:
    db = _db_dependency()
    try:
        payload = review_log_service.get_log(db, record_id=record_id)
        if payload is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review log not found")
        return ReviewLogRecordResponse(**payload)
    finally:
        db.close()

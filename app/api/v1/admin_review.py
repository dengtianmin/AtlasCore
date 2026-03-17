from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import require_roles
from app.auth.principal import Principal
from app.auth.rbac import ROLE_ADMIN
from app.db.session import get_db_session
from app.schemas.review import ReviewRubricResponse, ReviewRubricUpdateRequest
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

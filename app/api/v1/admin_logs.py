from collections.abc import Generator
from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.auth.dependencies import require_roles
from app.auth.principal import Principal
from app.auth.rbac import ROLE_ADMIN
from app.db.session import get_db_session
from app.schemas.logs import AdminLogListResponse, AdminLogRecordResponse, FeedbackRecordListResponse
from app.services.admin_log_service import AdminLogService

router = APIRouter(prefix="/api/admin/logs", tags=["admin-logs"])
service = AdminLogService()


def get_session() -> Generator[Session, None, None]:
    yield from get_db_session()


@router.get("", response_model=AdminLogListResponse)
def list_logs(
    _: Annotated[Principal, Depends(require_roles(ROLE_ADMIN))],
    db: Annotated[Session, Depends(get_session)],
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    keyword: str | None = Query(default=None),
    source: str | None = Query(default=None),
    liked: bool | None = Query(default=None),
    rating: int | None = Query(default=None, ge=1, le=5),
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
) -> AdminLogListResponse:
    return AdminLogListResponse(
        **service.list_logs(
            db,
            limit=limit,
            offset=offset,
            keyword=keyword,
            source=source,
            liked=liked,
            rating=rating,
            date_from=date_from,
            date_to=date_to,
        )
    )


@router.get("/feedback", response_model=FeedbackRecordListResponse)
def list_feedback(
    _: Annotated[Principal, Depends(require_roles(ROLE_ADMIN))],
    db: Annotated[Session, Depends(get_session)],
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> FeedbackRecordListResponse:
    return FeedbackRecordListResponse(**service.list_feedback(db, limit=limit, offset=offset))


@router.get("/{record_id}", response_model=AdminLogRecordResponse)
def get_log(
    record_id: UUID,
    _: Annotated[Principal, Depends(require_roles(ROLE_ADMIN))],
    db: Annotated[Session, Depends(get_session)],
) -> AdminLogRecordResponse:
    return AdminLogRecordResponse(**service.get_log(db, record_id=record_id))

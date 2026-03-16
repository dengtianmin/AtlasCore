from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_active_principal
from app.auth.principal import Principal
from app.db.session import get_db_session
from app.schemas.auth import CurrentAdminResponse, LoginRequest, TokenResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])
service = AuthService()


def _db_dependency() -> Session:
    try:
        session_gen = get_db_session()
        return next(session_gen)
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is not configured",
        ) from exc

@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest) -> TokenResponse:
    db = _db_dependency()
    try:
        return service.login(db, username=payload.username, password=payload.password)
    finally:
        db.close()


@router.get("/me", response_model=CurrentAdminResponse)
def me(
    principal: Annotated[Principal, Depends(get_current_active_principal)],
) -> CurrentAdminResponse:
    return CurrentAdminResponse(admin_id=principal.user_id, username=principal.username, roles=principal.roles)

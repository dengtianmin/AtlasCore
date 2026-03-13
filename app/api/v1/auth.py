from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_active_principal
from app.auth.principal import Principal
from app.db.session import get_db_session
from app.schemas.auth import CurrentUserResponse, LoginRequest, RegisterRequest, TokenResponse
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


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest) -> TokenResponse:
    db = _db_dependency()
    try:
        return service.register(db, email=payload.email, password=payload.password)
    finally:
        db.close()


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest) -> TokenResponse:
    db = _db_dependency()
    try:
        return service.login(db, email=payload.email, password=payload.password)
    finally:
        db.close()


@router.get("/me", response_model=CurrentUserResponse)
def me(
    principal: Annotated[Principal, Depends(get_current_active_principal)],
) -> CurrentUserResponse:
    return CurrentUserResponse(user_id=principal.user_id, email=principal.email, roles=principal.roles)

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_active_user_principal
from app.auth.principal import Principal
from app.db.session import get_db_session
from app.schemas.user import CurrentUserResponse, UserLoginRequest, UserRegisterRequest, UserTokenResponse
from app.services.user_auth_service import UserAuthService

router = APIRouter(prefix="/users", tags=["users"])
service = UserAuthService()


def _db_dependency() -> Session:
    try:
        session_gen = get_db_session()
        return next(session_gen)
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is not configured",
        ) from exc


@router.post("/register", response_model=CurrentUserResponse, status_code=status.HTTP_201_CREATED)
def register(payload: UserRegisterRequest) -> CurrentUserResponse:
    db = _db_dependency()
    try:
        return service.register(db, payload=payload)
    finally:
        db.close()


@router.post("/login", response_model=UserTokenResponse)
def login(payload: UserLoginRequest) -> UserTokenResponse:
    db = _db_dependency()
    try:
        return service.login(db, payload=payload)
    finally:
        db.close()


@router.get("/me", response_model=CurrentUserResponse)
def me(
    principal: Annotated[Principal, Depends(get_current_active_user_principal)],
) -> CurrentUserResponse:
    return service.get_current_user_payload(principal)


@router.get("/ping")
def user_ping() -> dict[str, str]:
    return {"status": "ok", "scope": "anonymous"}

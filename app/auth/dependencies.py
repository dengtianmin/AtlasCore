from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.logging import get_logger, log_event
from app.auth.identity import LocalJwtIdentityProvider, TokenIdentityProvider
from app.auth.jwt_handler import TokenDecodeError
from app.auth.principal import Principal
from app.db.session import get_db_session
from app.repositories.admin_account_repo import AdminAccountRepository

bearer_scheme = HTTPBearer(auto_error=True)
logger = get_logger(__name__)


def get_identity_provider() -> TokenIdentityProvider:
    # Future extension point: swap LocalJwtIdentityProvider with Entra provider.
    return LocalJwtIdentityProvider()


def _get_db_or_503() -> Session:
    try:
        session_gen = get_db_session()
        return next(session_gen)
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Auth backend not configured",
        ) from exc


def get_current_principal(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
    identity_provider: Annotated[TokenIdentityProvider, Depends(get_identity_provider)],
) -> Principal:
    try:
        payload = identity_provider.decode_token(credentials.credentials)
    except TokenDecodeError as exc:
        log_event(logger, 40, "admin_auth_failed", "failed", error_type="invalid_token", detail=str(exc))
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    roles = payload.get("roles", [])
    if not isinstance(roles, list):
        roles = []

    return Principal(
        user_id=str(payload["sub"]),
        username=str(payload.get("username", "")),
        roles=[str(role) for role in roles],
    )


def require_roles(*required_roles: str):
    def dependency(principal: Annotated[Principal, Depends(get_current_active_principal)]) -> Principal:
        if not any(role in principal.roles for role in required_roles):
            log_event(
                logger,
                40,
                "admin_auth_failed",
                "failed",
                error_type="insufficient_role",
                user_id=principal.user_id,
            )
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")
        return principal

    return dependency


def get_current_active_principal(
    principal: Annotated[Principal, Depends(get_current_principal)],
) -> Principal:
    # Minimal check against local user table. Safe to keep optional and swappable.
    db = _get_db_or_503()
    try:
        admin_repo = AdminAccountRepository()
        admin = admin_repo.get_by_id(db, UUID(principal.user_id))
        if admin is None:
            log_event(
                logger,
                40,
                "admin_auth_failed",
                "failed",
                error_type="admin_not_found",
                user_id=principal.user_id,
            )
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Admin not found")
        if not admin.is_active:
            log_event(
                logger,
                40,
                "admin_auth_failed",
                "failed",
                error_type="admin_inactive",
                user_id=principal.user_id,
            )
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin is inactive")
        principal.roles = ["admin"]
        principal.username = admin.username
        return principal
    finally:
        db.close()

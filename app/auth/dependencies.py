from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.auth.identity import LocalJwtIdentityProvider, TokenIdentityProvider
from app.auth.jwt_handler import TokenDecodeError
from app.auth.principal import Principal
from app.db.session import get_db_session
from app.repositories.user_repo import UserRepository

bearer_scheme = HTTPBearer(auto_error=True)


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
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    roles = payload.get("roles", [])
    if not isinstance(roles, list):
        roles = []

    return Principal(
        user_id=str(payload["sub"]),
        email=str(payload.get("email", "")),
        roles=[str(role) for role in roles],
    )


def require_roles(*required_roles: str):
    def dependency(principal: Annotated[Principal, Depends(get_current_active_principal)]) -> Principal:
        if not any(role in principal.roles for role in required_roles):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")
        return principal

    return dependency


def get_current_active_principal(
    principal: Annotated[Principal, Depends(get_current_principal)],
) -> Principal:
    # Minimal check against local user table. Safe to keep optional and swappable.
    db = _get_db_or_503()
    try:
        user_repo = UserRepository()
        user = user_repo.get_by_id(db, UUID(principal.user_id))
        if user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is inactive")
        principal.roles = user_repo.list_role_names(db, user.id)
        principal.email = user.email
        return principal
    finally:
        db.close()

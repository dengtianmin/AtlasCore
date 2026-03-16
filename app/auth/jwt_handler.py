from datetime import UTC, datetime, timedelta
from typing import Any

import jwt

from app.core.config import settings
from app.core.secrets import SecretResolutionError

JWT_ALGORITHM = "HS256"
DEFAULT_EXPIRES_MINUTES = 60


class TokenDecodeError(Exception):
    pass


def _resolve_jwt_secret() -> str:
    try:
        resolved_secret = settings.resolved_jwt_secret
    except SecretResolutionError as exc:
        raise TokenDecodeError("JWT secret is not configured") from exc
    if resolved_secret:
        return resolved_secret
    raise TokenDecodeError("JWT secret is not configured")


def create_access_token(*, subject: str, username: str, roles: list[str], expires_minutes: int = DEFAULT_EXPIRES_MINUTES) -> tuple[str, int]:
    expire_at = datetime.now(UTC) + timedelta(minutes=expires_minutes)
    payload: dict[str, Any] = {
        "sub": subject,
        "username": username,
        "roles": roles,
        "exp": expire_at,
        "iat": datetime.now(UTC),
        "iss": "atlascore-api",
    }
    token = jwt.encode(payload, _resolve_jwt_secret(), algorithm=JWT_ALGORITHM)
    return token, expires_minutes * 60


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(token, _resolve_jwt_secret(), algorithms=[JWT_ALGORITHM])
    except jwt.PyJWTError as exc:
        raise TokenDecodeError("Invalid or expired access token") from exc

    if "sub" not in payload:
        raise TokenDecodeError("Token missing subject")
    return payload

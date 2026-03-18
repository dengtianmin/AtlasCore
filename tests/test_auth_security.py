from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.auth.dependencies import get_current_active_principal, get_current_active_user_principal
from app.auth.jwt_handler import TokenDecodeError, create_access_token, decode_access_token
from app.auth.password import hash_password, verify_password
from app.auth.principal import Principal
from app.core.config import settings


def test_password_hash_and_verify():
    raw = "StrongPass123!"
    hashed = hash_password(raw)

    assert hashed != raw
    assert verify_password(raw, hashed) is True
    assert verify_password("wrong-pass", hashed) is False


def test_create_and_decode_access_token(monkeypatch):
    monkeypatch.setattr(settings, "JWT_SECRET", "unit-test-secret")
    monkeypatch.setattr(settings, "APP_ENV", "test")

    user_id = str(uuid4())
    token, expires_in = create_access_token(
        subject=user_id,
        username="admin-user",
        roles=["admin"],
        role="admin",
        scope="admin",
        token_type="admin_access",
    )

    payload = decode_access_token(token)
    assert payload["sub"] == user_id
    assert payload["username"] == "admin-user"
    assert payload["roles"] == ["admin"]
    assert payload["role"] == "admin"
    assert payload["scope"] == "admin"
    assert payload["token_type"] == "admin_access"
    assert payload["iss"] == "atlascore-api"
    assert expires_in == 3600


def test_decode_invalid_token_raises(monkeypatch):
    monkeypatch.setattr(settings, "JWT_SECRET", "unit-test-secret")
    monkeypatch.setattr(settings, "APP_ENV", "test")

    with pytest.raises(TokenDecodeError, match="Invalid or expired access token"):
        decode_access_token("not-a-valid-token")


def test_production_without_secret_rejected(monkeypatch):
    monkeypatch.setattr(settings, "JWT_SECRET", None)
    monkeypatch.setattr(settings, "JWT_SECRET_NAME", None)
    monkeypatch.setattr(settings, "APP_ENV", "production")

    with pytest.raises(TokenDecodeError, match="JWT secret is not configured"):
        create_access_token(
            subject="abc",
            username="admin-user",
            roles=["admin"],
            role="admin",
            scope="admin",
            token_type="admin_access",
        )


def test_test_environment_without_secret_rejected(monkeypatch):
    monkeypatch.setattr(settings, "JWT_SECRET", None)
    monkeypatch.setattr(settings, "JWT_SECRET_NAME", None)
    monkeypatch.setattr(settings, "APP_ENV", "test")

    with pytest.raises(TokenDecodeError, match="JWT secret is not configured"):
        create_access_token(
            subject="abc",
            username="admin-user",
            roles=["admin"],
            role="admin",
            scope="admin",
            token_type="admin_access",
        )


def test_user_scope_cannot_be_used_as_admin_token():
    principal = Principal(
        user_id=str(uuid4()),
        username="2025000001",
        student_id="2025000001",
        name="张三",
        roles=["user"],
        role="user",
        scope="user",
        token_type="user_access",
    )

    with pytest.raises(HTTPException, match="Admin token required") as exc_info:
        get_current_active_principal(principal)

    assert exc_info.value.status_code == 403


def test_admin_scope_cannot_be_used_as_user_token():
    principal = Principal(
        user_id=str(uuid4()),
        username="admin-user",
        roles=["admin"],
        role="admin",
        scope="admin",
        token_type="admin_access",
    )

    with pytest.raises(HTTPException, match="User token required") as exc_info:
        get_current_active_user_principal(principal)

    assert exc_info.value.status_code == 403

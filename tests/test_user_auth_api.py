from fastapi import HTTPException
from pydantic import ValidationError

from app.api.v1.users import login, me, register
from app.auth.principal import Principal
from app.core.config import settings
from app.core.lifespan import lifespan
from app.db.session import reset_db_state
from app.schemas.user import UserLoginRequest, UserRegisterRequest


async def _run_lifespan() -> None:
    from fastapi import FastAPI

    async with lifespan(FastAPI()):
        pass


def _bootstrap_runtime(monkeypatch, tmp_path) -> None:
    import asyncio

    monkeypatch.setattr(settings, "APP_ENV", "test")
    monkeypatch.setattr(settings, "JWT_SECRET", "unit-test-secret")
    monkeypatch.setattr(settings, "SQLITE_PATH", str(tmp_path / "runtime" / "atlascore.db"))
    monkeypatch.setattr(settings, "CSV_EXPORT_DIR", str(tmp_path / "exports"))
    monkeypatch.setattr(settings, "DOCUMENT_LOCAL_STORAGE_DIR", str(tmp_path / "uploads"))
    monkeypatch.setattr(settings, "INITIAL_ADMIN_USERNAME", "admin")
    monkeypatch.setattr(settings, "INITIAL_ADMIN_PASSWORD", "StrongPass123!")
    reset_db_state()
    asyncio.run(_run_lifespan())


def test_register_success(monkeypatch, tmp_path):
    _bootstrap_runtime(monkeypatch, tmp_path)

    payload = register(UserRegisterRequest(student_id="2025000001", name="张三", password="StrongPass123!"))

    assert payload.student_id == "2025000001"
    assert payload.name == "张三"
    assert payload.roles == ["user"]


def test_register_duplicate_student_id_rejected(monkeypatch, tmp_path):
    _bootstrap_runtime(monkeypatch, tmp_path)
    register(UserRegisterRequest(student_id="2025000001", name="张三", password="StrongPass123!"))

    try:
        register(UserRegisterRequest(student_id="2025000001", name="李四", password="StrongPass123!"))
    except HTTPException as exc:
        assert exc.status_code == 409
        assert exc.detail == "Student ID already registered"
    else:
        raise AssertionError("Expected duplicate student_id to be rejected")


def test_register_validation_failure():
    try:
        UserRegisterRequest(student_id="abc", name="Tom", password="short")
    except ValidationError as exc:
        message = str(exc)
        assert "student_id" in message
        assert "name" in message
        assert "password" in message
    else:
        raise AssertionError("Expected invalid registration payload to fail validation")


def test_login_success_and_me_payload(monkeypatch, tmp_path):
    _bootstrap_runtime(monkeypatch, tmp_path)
    created = register(UserRegisterRequest(student_id="2025000001", name="张三", password="StrongPass123!"))

    token = login(UserLoginRequest(student_id="2025000001", password="StrongPass123!"))
    assert token.access_token
    assert token.expires_in == 3600

    payload = me(
        Principal(
            user_id=created.user_id,
            username="2025000001",
            student_id="2025000001",
            name="张三",
            roles=["user"],
            role="user",
            scope="user",
            token_type="user_access",
        )
    )
    assert payload.student_id == "2025000001"
    assert payload.name == "张三"


def test_login_failure(monkeypatch, tmp_path):
    _bootstrap_runtime(monkeypatch, tmp_path)
    register(UserRegisterRequest(student_id="2025000001", name="张三", password="StrongPass123!"))

    try:
        login(UserLoginRequest(student_id="2025000001", password="wrong-pass"))
    except HTTPException as exc:
        assert exc.status_code == 401
        assert exc.detail == "Invalid credentials"
    else:
        raise AssertionError("Expected invalid credentials to be rejected")

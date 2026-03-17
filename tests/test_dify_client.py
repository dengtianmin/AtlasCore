import asyncio
import json
import logging

import httpx
import pytest

from app.core.config import settings
from app.integrations.dify.client import DifyClient
from app.integrations.dify.exceptions import (
    DifyAuthError,
    DifyBadRequestError,
    DifyFileTooLargeError,
    DifyQuotaExceededError,
    DifyServiceUnavailableError,
    DifyTimeoutError,
    DifyUnsupportedFileTypeError,
)


def _client(handler) -> DifyClient:
    transport = httpx.MockTransport(handler)
    return DifyClient(transport=transport)


def test_run_workflow_success(monkeypatch):
    monkeypatch.setattr(settings, "DIFY_BASE_URL", "https://dify.example.com")
    monkeypatch.setattr(settings, "DIFY_API_KEY", "api-key")
    monkeypatch.setattr(settings, "DIFY_API_KEY_SECRET_NAME", None)

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url == httpx.URL("https://dify.example.com/v1/workflows/run")
        assert request.headers["Authorization"] == "Bearer api-key"
        payload = json.loads(request.content.decode("utf-8"))
        assert payload["inputs"] == {"question": "hello"}
        assert payload["user"] == "guest-1"
        return httpx.Response(
            200,
            json={
                "workflow_run_id": "run-1",
                "task_id": "task-1",
                "data": {
                    "status": "succeeded",
                    "outputs": {"text": "world"},
                    "error": None,
                    "elapsed_time": 0.2,
                    "total_tokens": 12,
                    "total_steps": 2,
                },
            },
        )

    result = asyncio.run(_client(handler).run_workflow(inputs={"question": "hello"}, user="guest-1"))

    assert result.workflow_run_id == "run-1"
    assert result.task_id == "task-1"
    assert result.outputs["text"] == "world"
    assert result.total_tokens == 12


def test_upload_file_success(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "DIFY_BASE_URL", "https://dify.example.com")
    monkeypatch.setattr(settings, "DIFY_API_KEY", "api-key")
    monkeypatch.setattr(settings, "DIFY_API_KEY_SECRET_NAME", None)
    file_path = tmp_path / "doc.txt"
    file_path.write_text("atlas", encoding="utf-8")

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url == httpx.URL("https://dify.example.com/v1/files/upload")
        assert b'name="user"' in request.content
        assert b'name="file"; filename="doc.txt"' in request.content
        return httpx.Response(
            200,
            json={
                "id": "file-1",
                "name": "doc.txt",
                "size": 5,
                "extension": "txt",
                "mime_type": "text/plain",
                "created_at": 123,
            },
        )

    uploaded = asyncio.run(_client(handler).upload_file(str(file_path), user="guest-2", mime_type="text/plain"))

    assert uploaded.file_id == "file-1"
    assert uploaded.name == "doc.txt"
    assert uploaded.mime_type == "text/plain"


def test_get_parameters_success(monkeypatch):
    monkeypatch.setattr(settings, "DIFY_BASE_URL", "https://dify.example.com")
    monkeypatch.setattr(settings, "DIFY_API_KEY", "api-key")
    monkeypatch.setattr(settings, "DIFY_API_KEY_SECRET_NAME", None)

    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"user_input_form": [{"variable": "question"}]})

    payload = asyncio.run(_client(handler).get_parameters())

    assert payload["user_input_form"][0]["variable"] == "question"


def test_validate_configuration_success(monkeypatch):
    monkeypatch.setattr(settings, "DIFY_BASE_URL", "https://dify.example.com")
    monkeypatch.setattr(settings, "DIFY_API_KEY", "api-key")
    monkeypatch.setattr(settings, "DIFY_API_KEY_SECRET_NAME", None)
    monkeypatch.setattr(settings, "DIFY_TEXT_INPUT_VARIABLE", "question")
    monkeypatch.setattr(settings, "DIFY_FILE_INPUT_VARIABLE", "attachments")

    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "user_input_form": [
                    {"variable": "question"},
                    {"variable": "attachments"},
                ],
                "features": {"file_upload": {"enabled": True}},
            },
        )

    result = asyncio.run(_client(handler).validate_configuration())

    assert result.ok is True
    assert result.text_input_variable_exists is True
    assert result.file_input_variable_exists is True
    assert result.file_upload_enabled is True


def test_validate_configuration_reports_missing_variable(monkeypatch):
    monkeypatch.setattr(settings, "DIFY_BASE_URL", "https://dify.example.com")
    monkeypatch.setattr(settings, "DIFY_API_KEY", "api-key")
    monkeypatch.setattr(settings, "DIFY_API_KEY_SECRET_NAME", None)
    monkeypatch.setattr(settings, "DIFY_TEXT_INPUT_VARIABLE", "question")
    monkeypatch.setattr(settings, "DIFY_FILE_INPUT_VARIABLE", "attachments")

    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "user_input_form": [{"variable": "question"}],
                "features": {"file_upload": {"enabled": False}},
            },
        )

    result = asyncio.run(_client(handler).validate_configuration())

    assert result.ok is False
    assert result.file_input_variable_exists is False
    assert result.file_upload_enabled is False
    assert len(result.warnings) == 2


def test_http_error_mapping(monkeypatch):
    monkeypatch.setattr(settings, "DIFY_BASE_URL", "https://dify.example.com")
    monkeypatch.setattr(settings, "DIFY_API_KEY", "api-key")
    monkeypatch.setattr(settings, "DIFY_API_KEY_SECRET_NAME", None)

    def auth_handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"code": "unauthorized", "message": "bad token"})

    def quota_handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(429, json={"code": "rate_limit", "message": "too many"})

    with pytest.raises(DifyAuthError):
        asyncio.run(_client(auth_handler).get_parameters())
    with pytest.raises(DifyQuotaExceededError):
        asyncio.run(_client(quota_handler).get_parameters())


def test_dify_business_error_mapping(monkeypatch):
    monkeypatch.setattr(settings, "DIFY_BASE_URL", "https://dify.example.com")
    monkeypatch.setattr(settings, "DIFY_API_KEY", "api-key")
    monkeypatch.setattr(settings, "DIFY_API_KEY_SECRET_NAME", None)

    def large_file_handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(400, json={"code": "file_too_large", "message": "too large"})

    def unsupported_handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(400, json={"code": "unsupported_file_type", "message": "bad type"})

    with pytest.raises(DifyFileTooLargeError):
        asyncio.run(_client(large_file_handler).get_parameters())
    with pytest.raises(DifyUnsupportedFileTypeError):
        asyncio.run(_client(unsupported_handler).get_parameters())


def test_timeout_handling(monkeypatch):
    monkeypatch.setattr(settings, "DIFY_BASE_URL", "https://dify.example.com")
    monkeypatch.setattr(settings, "DIFY_API_KEY", "api-key")
    monkeypatch.setattr(settings, "DIFY_API_KEY_SECRET_NAME", None)

    def handler(_: httpx.Request):
        raise httpx.ReadTimeout("timed out")

    with pytest.raises(DifyTimeoutError):
        asyncio.run(_client(handler).get_parameters())


def test_retry_only_for_transient_errors(monkeypatch):
    monkeypatch.setattr(settings, "DIFY_BASE_URL", "https://dify.example.com")
    monkeypatch.setattr(settings, "DIFY_API_KEY", "api-key")
    monkeypatch.setattr(settings, "DIFY_API_KEY_SECRET_NAME", None)
    calls = {"count": 0}

    def transient_handler(_: httpx.Request) -> httpx.Response:
        calls["count"] += 1
        if calls["count"] == 1:
            return httpx.Response(503, json={"code": "unavailable", "message": "retry"})
        return httpx.Response(200, json={"user_input_form": []})

    payload = asyncio.run(_client(transient_handler).get_parameters())

    assert calls["count"] == 2
    assert payload == {"user_input_form": []}


def test_non_retryable_bad_request(monkeypatch):
    monkeypatch.setattr(settings, "DIFY_BASE_URL", "https://dify.example.com")
    monkeypatch.setattr(settings, "DIFY_API_KEY", "api-key")
    monkeypatch.setattr(settings, "DIFY_API_KEY_SECRET_NAME", None)
    calls = {"count": 0}

    def handler(_: httpx.Request) -> httpx.Response:
        calls["count"] += 1
        return httpx.Response(422, json={"code": "invalid_param", "message": "bad param"})

    with pytest.raises(DifyBadRequestError):
        asyncio.run(_client(handler).get_parameters())

    assert calls["count"] == 1


def test_logging_does_not_leak_sensitive_information(monkeypatch, caplog):
    monkeypatch.setattr(settings, "DIFY_BASE_URL", "https://dify.example.com")
    monkeypatch.setattr(settings, "DIFY_API_KEY", "secret-api-key")
    monkeypatch.setattr(settings, "DIFY_API_KEY_SECRET_NAME", None)

    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(503, json={"code": "upstream", "message": "provider failed"})

    with caplog.at_level(logging.INFO):
        with pytest.raises(DifyServiceUnavailableError):
            asyncio.run(_client(handler).get_parameters())

    joined = "\n".join(record.getMessage() for record in caplog.records)
    assert "secret-api-key" not in joined
    assert "Bearer secret-api-key" not in joined

import asyncio
import json

from fastapi import FastAPI, Request

from app.core.exceptions import AppException, register_exception_handlers


def _fake_request() -> Request:
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": "/",
        "raw_path": b"/",
        "query_string": b"",
        "headers": [],
        "client": ("127.0.0.1", 12345),
        "server": ("127.0.0.1", 8000),
    }
    return Request(scope)


def test_app_exception_handler_returns_expected_json():
    app = FastAPI()
    register_exception_handlers(app)

    handler = app.exception_handlers[AppException]
    response = asyncio.run(handler(_fake_request(), AppException("bad request", status_code=418)))
    payload = json.loads(response.body)

    assert response.status_code == 418
    assert payload == {
        "error": {
            "type": "app_error",
            "message": "bad request",
        }
    }


def test_unhandled_exception_handler_returns_500_json():
    app = FastAPI()
    register_exception_handlers(app)

    handler = app.exception_handlers[Exception]
    response = asyncio.run(handler(_fake_request(), RuntimeError("boom")))
    payload = json.loads(response.body)

    assert response.status_code == 500
    assert payload == {
        "error": {
            "type": "internal_server_error",
            "message": "Unexpected server error",
        }
    }

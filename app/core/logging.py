from __future__ import annotations

import json
import logging
from typing import Any

from app.core.config import settings

_SENSITIVE_TOKENS = ("secret", "password", "token", "api_key", "jwt", "authorization")


def _sanitize(value: Any) -> Any:
    if isinstance(value, dict):
        sanitized: dict[str, Any] = {}
        for key, item in value.items():
            if any(token in key.lower() for token in _SENSITIVE_TOKENS):
                sanitized[key] = "***"
            else:
                sanitized[key] = _sanitize(item)
        return sanitized
    if isinstance(value, list):
        return [_sanitize(item) for item in value]
    return value


def setup_logging() -> None:
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL, logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        force=True,
    )


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def log_event(logger: logging.Logger, level: int, event: str, status: str, **fields: Any) -> None:
    payload = {"event": event, "status": status, **_sanitize(fields)}
    logger.log(level, json.dumps(payload, default=str, ensure_ascii=True, sort_keys=True))

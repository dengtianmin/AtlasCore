import json
import logging

from app.core.logging import log_event


def test_log_event_masks_secrets(caplog):
    logger = logging.getLogger("tests.logging")

    with caplog.at_level(logging.INFO):
        log_event(
            logger,
            logging.INFO,
            "config_summary",
            "success",
            jwt_secret="top-secret",
            nested={"api_key": "abc123", "status": "ok"},
        )

    message = caplog.records[0].getMessage()
    payload = json.loads(message)
    assert payload["jwt_secret"] == "***"
    assert payload["nested"]["api_key"] == "***"
    assert "top-secret" not in message
    assert "abc123" not in message

from app.api.v1.health import health_check
from app.core.config import settings


def test_health_check_payload(monkeypatch):
    monkeypatch.setattr(settings, "APP_NAME", "AtlasCore API")

    payload = health_check()

    assert payload == {"status": "ok", "service": "AtlasCore API"}

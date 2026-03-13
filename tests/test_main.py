from app.core.config import settings
from app.core.exceptions import AppException
from app.main import create_app


def test_create_app_uses_settings_metadata(monkeypatch):
    monkeypatch.setattr(settings, "APP_NAME", "AtlasCore API")
    monkeypatch.setattr(settings, "APP_VERSION", "0.1.0")
    monkeypatch.setattr(settings, "APP_ENV", "production")

    app = create_app()

    assert app.title == "AtlasCore API"
    assert app.version == "0.1.0"
    assert app.debug is False


def test_health_route_registered(app_instance):
    route_paths = {route.path for route in app_instance.routes}
    assert "/health" in route_paths


def test_exception_handlers_registered(app_instance):
    assert AppException in app_instance.exception_handlers
    assert Exception in app_instance.exception_handlers

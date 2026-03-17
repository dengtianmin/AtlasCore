import asyncio

from app.api.v1.health import health_check, readiness_check
from app.core.config import settings
from app.services.runtime_status_service import runtime_status_service


def test_health_check_payload():
    payload = health_check()

    assert payload == {"status": "ok"}


def test_readiness_check_payload(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "APP_ENV", "test")
    monkeypatch.setattr(settings, "JWT_SECRET", "unit-test-secret")
    monkeypatch.setattr(settings, "SQLITE_PATH", str(tmp_path / "runtime" / "atlascore.db"))
    monkeypatch.setattr(settings, "CSV_EXPORT_DIR", str(tmp_path / "exports"))
    monkeypatch.setattr(settings, "DOCUMENT_LOCAL_STORAGE_DIR", str(tmp_path / "uploads"))
    monkeypatch.setattr(settings, "GRAPH_EXPORT_DIR", str(tmp_path / "graph_exports"))
    monkeypatch.setattr(settings, "GRAPH_IMPORT_DIR", str(tmp_path / "graph_imports"))
    monkeypatch.setattr(settings, "GRAPH_INSTANCE_LOCAL_PATH", str(tmp_path / "graph" / "atlascore_graph.db"))
    monkeypatch.setattr(settings, "GRAPH_INSTANCE_ID", "ready-instance")
    monkeypatch.setattr(settings, "GRAPH_DB_VERSION", "v-ready")
    runtime_status_service.reset()
    runtime_status_service.mark_config_loaded()

    payload = asyncio.run(readiness_check())

    assert payload["app_env"] == "test"
    assert payload["current_mode"] == "test"
    assert payload["graph_instance_id"] == "ready-instance"
    assert payload["graph_db_version"] == "v-ready"
    assert payload["app_ready"] is False
    assert payload["config_loaded"] is True
    assert payload["dify_configured"] is False
    assert payload["dify_reachable"] is False
    assert "unit-test-secret" not in str(payload)

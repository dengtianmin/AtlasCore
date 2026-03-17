import asyncio

from app.api.v1.admin_system import get_system_status
from app.auth.principal import Principal
from app.core.config import settings
from app.services.runtime_status_service import runtime_status_service


def _admin() -> Principal:
    return Principal(user_id="00000000-0000-0000-0000-000000000001", username="admin", roles=["admin"])


def test_admin_system_status_contains_integration_fields(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "APP_ENV", "test")
    monkeypatch.setattr(settings, "JWT_SECRET", "unit-test-secret")
    monkeypatch.setattr(settings, "SQLITE_PATH", str(tmp_path / "runtime" / "atlascore.db"))
    monkeypatch.setattr(settings, "CSV_EXPORT_DIR", str(tmp_path / "exports"))
    monkeypatch.setattr(settings, "DOCUMENT_LOCAL_STORAGE_DIR", str(tmp_path / "uploads"))
    monkeypatch.setattr(settings, "GRAPH_EXPORT_DIR", str(tmp_path / "graph_exports"))
    monkeypatch.setattr(settings, "GRAPH_IMPORT_DIR", str(tmp_path / "graph_imports"))
    monkeypatch.setattr(settings, "GRAPH_INSTANCE_LOCAL_PATH", str(tmp_path / "graph" / "atlascore_graph.db"))
    monkeypatch.setattr(settings, "GRAPH_INSTANCE_ID", "status-instance")
    monkeypatch.setattr(settings, "GRAPH_DB_VERSION", "status-v1")
    runtime_status_service.reset()
    runtime_status_service.mark_config_loaded()

    payload = asyncio.run(get_system_status(_=_admin()))

    assert payload["graph_instance_id"] == "status-instance"
    assert payload["graph_db_version"] == "status-v1"
    assert payload["dify_reachable"] is False
    assert payload["dify_validation_ok"] is False
    assert payload["multi_instance_rule"] == "no_shared_graph_sqlite"
    assert "unit-test-secret" not in str(payload)

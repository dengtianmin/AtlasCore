from datetime import UTC, datetime

from app.core.config import settings
from app.services.runtime_status_service import RuntimeStatusService


def test_runtime_status_service_tracks_graph_and_exports(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "APP_ENV", "test")
    monkeypatch.setattr(settings, "JWT_SECRET", "unit-test-secret")
    monkeypatch.setattr(settings, "SQLITE_PATH", str(tmp_path / "runtime" / "atlascore.db"))
    monkeypatch.setattr(settings, "CSV_EXPORT_DIR", str(tmp_path / "exports"))
    monkeypatch.setattr(settings, "DOCUMENT_LOCAL_STORAGE_DIR", str(tmp_path / "uploads"))
    monkeypatch.setattr(settings, "GRAPH_EXPORT_DIR", str(tmp_path / "graph_exports"))
    monkeypatch.setattr(settings, "GRAPH_IMPORT_DIR", str(tmp_path / "graph_imports"))
    monkeypatch.setattr(settings, "GRAPH_INSTANCE_LOCAL_PATH", str(tmp_path / "graph" / "atlascore_graph.db"))
    monkeypatch.setattr(settings, "GRAPH_INSTANCE_ID", "instance-test")
    monkeypatch.setattr(settings, "GRAPH_DB_VERSION", "v20260317")
    monkeypatch.setattr(settings, "GRAPH_ENABLED", True)
    monkeypatch.setattr(settings, "DIFY_BASE_URL", None)
    monkeypatch.setattr(settings, "DIFY_API_KEY", None)

    service = RuntimeStatusService()
    service.mark_config_loaded()
    service.mark_sqlite_ready()
    service.mark_migration_ready()
    loaded_at = datetime.now(UTC)
    service.mark_graph_status(loaded=True, node_count=5, edge_count=9, loaded_at=loaded_at)
    service.record_graph_import({"status": "success", "filename": "import.db"})
    service.record_graph_export({"status": "success", "filename": "export.db"})
    service.record_csv_export({"status": "success", "filename": "qa.csv"})

    payload = service.get_admin_status()

    assert payload["app_ready"] is True
    assert payload["config_loaded"] is True
    assert payload["sqlite_ready"] is True
    assert payload["migration_ready"] is True
    assert payload["graph_loaded"] is True
    assert payload["graph_node_count"] == 5
    assert payload["graph_edge_count"] == 9
    assert payload["graph_instance_id"] == "instance-test"
    assert payload["graph_db_version"] == "v20260317"
    assert payload["graph_instance_local_path_exists"] is False
    assert payload["graph_import_dir_readable"] is True
    assert payload["graph_export_dir_writable"] is True
    assert payload["csv_export_ready"] is True
    assert payload["admin_auth_ready"] is False
    assert payload["document_module_ready"] is True
    assert payload["last_graph_import"]["filename"] == "import.db"
    assert payload["last_graph_export"]["filename"] == "export.db"
    assert payload["last_csv_export"]["filename"] == "qa.csv"
    assert payload["multi_instance_rule"] == "no_shared_graph_sqlite"

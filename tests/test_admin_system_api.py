import asyncio

from app.api.v1.admin_system import get_system_status
from app.auth.principal import Principal
from app.core.config import settings
from app.integrations.dify.schemas import DifyValidationResult
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
    monkeypatch.setattr(settings, "DIFY_FILE_INPUT_VARIABLE", "attachments")

    class StubDifyClient:
        def is_enabled(self) -> bool:
            return True

        async def validate_configuration(self):
            return DifyValidationResult(
                ok=True,
                reachable=True,
                text_input_variable_exists=True,
                file_input_variable_exists=True,
                file_upload_enabled=True,
                warnings=[],
                raw_parameters={
                    "user_input_form": [
                        {"variable": "query", "type": "text-input"},
                        {"variable": "attachments", "type": "file"},
                    ],
                    "features": {"file_upload": {"enabled": True}},
                    "file_upload": {
                        "number_limits": 3,
                        "file_size_limit": 10485760,
                        "allowed_file_extensions": [".pdf", ".txt"],
                    },
                },
            )

    monkeypatch.setattr("app.services.runtime_status_service.get_dify_client", lambda: StubDifyClient())
    runtime_status_service.reset()
    runtime_status_service.mark_config_loaded()

    payload = asyncio.run(get_system_status(_=_admin()))

    assert payload["graph_instance_id"] == "status-instance"
    assert payload["graph_db_version"] == "status-v1"
    assert payload["dify_reachable"] is True
    assert payload["dify_validation_ok"] is True
    assert payload["dify_file_input_enabled"] is True
    assert payload["dify_file_input_variable"] == "attachments"
    assert payload["dify_file_upload_limits"]["max_files"] == 3
    assert payload["multi_instance_rule"] == "no_shared_graph_sqlite"
    assert "unit-test-secret" not in str(payload)

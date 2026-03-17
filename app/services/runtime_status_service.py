from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from datetime import UTC, datetime
from threading import RLock
from typing import Any

from app.core.config import settings
from app.integrations.dify import DifyClientError, DifyConfigurationError, get_dify_client


@dataclass(slots=True)
class RuntimeStatusState:
    started_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    config_loaded: bool = False
    sqlite_ready: bool = False
    migration_ready: bool = False
    graph_enabled: bool = False
    graph_loaded: bool = False
    graph_node_count: int = 0
    graph_edge_count: int = 0
    last_graph_load_at: datetime | None = None
    last_graph_import: dict[str, Any] | None = None
    last_graph_export: dict[str, Any] | None = None
    last_csv_export: dict[str, Any] | None = None
    last_error: dict[str, Any] | None = None


class RuntimeStatusService:
    def __init__(self) -> None:
        self._lock = RLock()
        self._state = RuntimeStatusState(graph_enabled=settings.GRAPH_ENABLED)

    def reset(self) -> None:
        with self._lock:
            self._state = RuntimeStatusState(graph_enabled=settings.GRAPH_ENABLED)

    def mark_config_loaded(self) -> None:
        with self._lock:
            self._state.config_loaded = True
            self._state.graph_enabled = settings.GRAPH_ENABLED

    def mark_sqlite_ready(self) -> None:
        with self._lock:
            self._state.sqlite_ready = True

    def mark_migration_ready(self) -> None:
        with self._lock:
            self._state.migration_ready = True

    def mark_graph_status(
        self,
        *,
        loaded: bool,
        node_count: int = 0,
        edge_count: int = 0,
        loaded_at: datetime | None = None,
    ) -> None:
        with self._lock:
            self._state.graph_enabled = settings.GRAPH_ENABLED
            self._state.graph_loaded = loaded
            self._state.graph_node_count = node_count
            self._state.graph_edge_count = edge_count
            self._state.last_graph_load_at = loaded_at

    def record_graph_import(self, payload: dict[str, Any]) -> None:
        with self._lock:
            self._state.last_graph_import = deepcopy(payload)

    def record_graph_export(self, payload: dict[str, Any]) -> None:
        with self._lock:
            self._state.last_graph_export = deepcopy(payload)

    def record_csv_export(self, payload: dict[str, Any]) -> None:
        with self._lock:
            self._state.last_csv_export = deepcopy(payload)

    def record_error(self, *, error_type: str, detail: str) -> None:
        with self._lock:
            self._state.last_error = {
                "error_type": error_type,
                "detail": detail,
                "recorded_at": datetime.now(UTC),
            }

    async def get_status(self) -> dict[str, Any]:
        return await self.get_public_status()

    async def get_public_status(self) -> dict[str, Any]:
        base = await self._build_status_base(include_sensitive_paths=False)
        return {
            "app_ready": base["app_ready"],
            "sqlite_ready": base["sqlite_ready"],
            "dify_configured": base["dify_configured"],
            "dify_reachable": base["dify_reachable"],
            "dify_validation_ok": base["dify_validation_ok"],
            "dify_file_input_enabled": base["dify_file_input_enabled"],
            "dify_file_input_variable": base["dify_file_input_variable"],
            "graph_enabled": base["graph_enabled"],
            "graph_loaded": base["graph_loaded"],
            "graph_node_count": base["graph_node_count"],
            "graph_edge_count": base["graph_edge_count"],
            "graph_instance_id": base["graph_instance_id"],
            "graph_db_version": base["graph_db_version"],
            "graph_instance_local_path_exists": base["graph_instance_local_path_exists"],
            "csv_export_ready": base["csv_export_ready"],
            "admin_auth_ready": base["admin_auth_ready"],
            "document_module_ready": base["document_module_ready"],
            "current_mode": base["current_mode"],
            "app_env": base["app_env"],
            "config_loaded": base["config_loaded"],
            "migration_ready": base["migration_ready"],
            "started_at": base["started_at"],
            "uptime_seconds": base["uptime_seconds"],
            "last_graph_load_at": base["last_graph_load_at"],
            "last_graph_import": base["last_graph_import"],
            "last_graph_export": base["last_graph_export"],
            "last_csv_export": base["last_csv_export"],
            "last_error": base["last_error"],
        }

    async def get_admin_status(self) -> dict[str, Any]:
        return await self._build_status_base(include_sensitive_paths=True)

    async def _build_status_base(self, *, include_sensitive_paths: bool) -> dict[str, Any]:
        with self._lock:
            state = deepcopy(self._state)

        config_summary = settings.runtime_config_summary()
        paths = config_summary["paths"]
        now = datetime.now(UTC)
        dify_status = await self._get_dify_status()
        csv_export_ready = bool(paths["csv_export_dir"]["writable"])
        graph_instance_local_path_exists = paths["graph_instance_local_path"]["exists"]
        admin_auth_ready = config_summary["admin_auth_configured"]
        document_module_ready = bool(paths["document_storage_dir"]["writable"])
        app_ready = (
            state.config_loaded
            and state.sqlite_ready
            and state.migration_ready
            and csv_export_ready
            and document_module_ready
        )
        payload = {
            "app_ready": app_ready,
            "app_env": settings.APP_ENV,
            "current_mode": settings.APP_ENV,
            "app_name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "config_loaded": state.config_loaded,
            "sqlite_ready": state.sqlite_ready,
            "migration_ready": state.migration_ready,
            "graph_enabled": settings.GRAPH_ENABLED,
            "graph_loaded": state.graph_loaded,
            "graph_node_count": state.graph_node_count,
            "graph_edge_count": state.graph_edge_count,
            "graph_instance_id": settings.GRAPH_INSTANCE_ID,
            "graph_db_version": settings.GRAPH_DB_VERSION,
            "graph_instance_local_path_exists": graph_instance_local_path_exists,
            "graph_import_dir_readable": bool(paths["graph_import_dir"]["readable"]),
            "graph_export_dir_writable": bool(paths["graph_export_dir"]["writable"]),
            "csv_export_ready": csv_export_ready,
            "csv_export_dir_writable": csv_export_ready,
            "dify_configured": config_summary["dify_configured"],
            "dify_reachable": dify_status["reachable"],
            "dify_validation_ok": dify_status["ok"],
            "dify_validation_warnings": dify_status["warnings"],
            "dify_file_input_enabled": dify_status["file_input_enabled"],
            "dify_file_input_variable": dify_status["file_input_variable"],
            "dify_file_input_variable_exists": dify_status["file_input_variable_exists"],
            "dify_file_upload_limits": dify_status["file_limits"],
            "admin_auth_ready": admin_auth_ready,
            "admin_auth_configured": admin_auth_ready,
            "document_module_ready": document_module_ready,
            "started_at": state.started_at,
            "uptime_seconds": int((now - state.started_at).total_seconds()),
            "last_graph_load_at": state.last_graph_load_at,
            "last_graph_import": state.last_graph_import,
            "last_graph_export": state.last_graph_export,
            "last_csv_export": state.last_csv_export,
            "last_error": state.last_error,
            "graph_runtime_rule": "instance_local_sqlite_only",
            "multi_instance_rule": "no_shared_graph_sqlite",
        }
        if include_sensitive_paths:
            payload["paths"] = paths
            payload["graph_instance_local_path"] = paths["graph_instance_local_path"]["path"]
            payload["graph_snapshot_path"] = paths["graph_snapshot_path"]["path"]
            payload["csv_export_dir"] = paths["csv_export_dir"]["path"]
            payload["document_storage_dir"] = paths["document_storage_dir"]["path"]
            payload["dify_parameters"] = dify_status["parameters"]
        return payload

    @staticmethod
    async def _get_dify_status() -> dict[str, Any]:
        try:
            client = get_dify_client()
            if not client.is_enabled():
                return {
                    "reachable": False,
                    "ok": False,
                    "warnings": [],
                    "parameters": {},
                    "file_input_enabled": False,
                    "file_input_variable": settings.DIFY_FILE_INPUT_VARIABLE,
                    "file_input_variable_exists": False,
                    "file_limits": {},
                }
            validation = await client.validate_configuration()
            file_capabilities = RuntimeStatusService._extract_file_capabilities(validation.raw_parameters)
            return {
                "reachable": validation.reachable,
                "ok": validation.ok,
                "warnings": validation.warnings,
                "parameters": validation.raw_parameters,
                "file_input_enabled": validation.file_upload_enabled,
                "file_input_variable": settings.DIFY_FILE_INPUT_VARIABLE or file_capabilities["variable"],
                "file_input_variable_exists": validation.file_input_variable_exists,
                "file_limits": file_capabilities["limits"],
            }
        except DifyConfigurationError:
            return {
                "reachable": False,
                "ok": False,
                "warnings": [],
                "parameters": {},
                "file_input_enabled": False,
                "file_input_variable": settings.DIFY_FILE_INPUT_VARIABLE,
                "file_input_variable_exists": False,
                "file_limits": {},
            }
        except DifyClientError as exc:
            return {
                "reachable": False,
                "ok": False,
                "warnings": [str(exc)],
                "parameters": {},
                "file_input_enabled": False,
                "file_input_variable": settings.DIFY_FILE_INPUT_VARIABLE,
                "file_input_variable_exists": False,
                "file_limits": {},
            }
        except Exception:
            return {
                "reachable": False,
                "ok": False,
                "warnings": ["unexpected_dify_status_error"],
                "parameters": {},
                "file_input_enabled": False,
                "file_input_variable": settings.DIFY_FILE_INPUT_VARIABLE,
                "file_input_variable_exists": False,
                "file_limits": {},
            }

    @staticmethod
    def _extract_file_capabilities(parameters: dict[str, Any]) -> dict[str, Any]:
        files = parameters.get("file_upload") or parameters.get("files") or {}
        features = parameters.get("features") or {}
        feature_files = features.get("file_upload") if isinstance(features, dict) else {}
        file_settings = files if isinstance(files, dict) else {}
        if isinstance(feature_files, dict):
            file_settings = {**feature_files, **file_settings}

        variable = settings.DIFY_FILE_INPUT_VARIABLE
        user_input_form = parameters.get("user_input_form") or []
        if not variable:
            variable = RuntimeStatusService._find_file_variable(user_input_form)

        limits = {
            "max_files": file_settings.get("number_limits") or file_settings.get("max_files"),
            "max_file_size": file_settings.get("file_size_limit") or file_settings.get("max_file_size"),
            "allowed_file_types": file_settings.get("allowed_file_extensions")
            or file_settings.get("allowed_file_types")
            or file_settings.get("allowed_extensions"),
        }
        return {"variable": variable, "limits": {k: v for k, v in limits.items() if v is not None}}

    @staticmethod
    def _find_file_variable(value: Any) -> str | None:
        if isinstance(value, dict):
            candidate_type = value.get("type") or value.get("input_type")
            candidate_variable = value.get("variable") or value.get("name")
            if isinstance(candidate_type, str) and "file" in candidate_type and isinstance(candidate_variable, str):
                return candidate_variable
            for nested in value.values():
                found = RuntimeStatusService._find_file_variable(nested)
                if found:
                    return found
        if isinstance(value, list):
            for item in value:
                found = RuntimeStatusService._find_file_variable(item)
                if found:
                    return found
        return None


runtime_status_service = RuntimeStatusService()

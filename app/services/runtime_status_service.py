from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from datetime import UTC, datetime
from threading import RLock
from typing import Any

from app.core.config import settings
from app.integrations.dify import DifyConfigurationError, get_dify_client


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

    def get_status(self) -> dict[str, Any]:
        return self.get_public_status()

    def get_public_status(self) -> dict[str, Any]:
        base = self._build_status_base(include_sensitive_paths=False)
        return {
            "app_ready": base["app_ready"],
            "sqlite_ready": base["sqlite_ready"],
            "dify_configured": base["dify_configured"],
            "dify_reachable": base["dify_reachable"],
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

    def get_admin_status(self) -> dict[str, Any]:
        return self._build_status_base(include_sensitive_paths=True)

    def _build_status_base(self, *, include_sensitive_paths: bool) -> dict[str, Any]:
        with self._lock:
            state = deepcopy(self._state)

        config_summary = settings.runtime_config_summary()
        paths = config_summary["paths"]
        now = datetime.now(UTC)
        dify_reachable = self._get_dify_reachable()
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
            "dify_reachable": dify_reachable,
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
        return payload

    @staticmethod
    def _get_dify_reachable() -> bool:
        try:
            client = get_dify_client()
            if not client.is_enabled():
                return False
            return bool(client.check_reachable())
        except DifyConfigurationError:
            return False
        except Exception:
            return False


runtime_status_service = RuntimeStatusService()

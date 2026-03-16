from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from datetime import UTC, datetime
from threading import RLock
from typing import Any

from app.core.config import settings


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
        with self._lock:
            state = deepcopy(self._state)

        config_summary = settings.runtime_config_summary()
        paths = config_summary["paths"]
        now = datetime.now(UTC)
        return {
            "app_env": settings.APP_ENV,
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
            "graph_instance_local_path_exists": paths["graph_instance_local_path"]["exists"],
            "graph_import_dir_readable": bool(paths["graph_import_dir"]["readable"]),
            "graph_export_dir_writable": bool(paths["graph_export_dir"]["writable"]),
            "csv_export_dir_writable": bool(paths["csv_export_dir"]["writable"]),
            "dify_configured": config_summary["dify_configured"],
            "admin_auth_configured": config_summary["admin_auth_configured"],
            "started_at": state.started_at,
            "uptime_seconds": int((now - state.started_at).total_seconds()),
            "last_graph_load_at": state.last_graph_load_at,
            "last_graph_import": state.last_graph_import,
            "last_graph_export": state.last_graph_export,
            "last_csv_export": state.last_csv_export,
            "last_error": state.last_error,
        }


runtime_status_service = RuntimeStatusService()

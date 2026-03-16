import os
import shutil
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import quote

from fastapi import UploadFile
from fastapi import HTTPException, status

from app.core.config import settings
from app.graph.db import get_graph_session_factory, initialize_graph_database, reset_graph_db_state
from app.graph.exceptions import GraphImportError, GraphNodeNotFoundError, GraphUnavailableError
from app.graph.graph_runtime import GraphRuntime
from app.repositories.graph_repo import GraphRepository

_runtime = GraphRuntime()
_required_tables = {"graph_nodes", "graph_edges", "graph_sync_records", "graph_versions"}


class GraphService:
    def __init__(self, runtime: GraphRuntime | None = None) -> None:
        self.runtime = runtime or _runtime
        self.repo = GraphRepository()

    def get_summary(self) -> dict:
        try:
            return self.runtime.load_graph()
        except GraphUnavailableError as exc:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc

    def reload_graph(self) -> dict:
        try:
            return self.runtime.reload_graph()
        except GraphUnavailableError as exc:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc

    def get_admin_status(self) -> dict:
        summary = self.runtime.get_graph_summary()
        return {
            **summary,
            "enabled": settings.GRAPH_ENABLED,
            "import_dir": settings.GRAPH_IMPORT_DIR,
            "export_dir": settings.GRAPH_EXPORT_DIR,
            "import_dir_exists": Path(settings.GRAPH_IMPORT_DIR).expanduser().exists(),
            "export_dir_exists": Path(settings.GRAPH_EXPORT_DIR).expanduser().exists(),
            "instance_local_path": str(settings.graph_instance_path),
        }

    def export_graph_sqlite(self) -> dict:
        self.runtime.load_graph()
        export_dir = Path(settings.GRAPH_EXPORT_DIR).expanduser()
        export_dir.mkdir(parents=True, exist_ok=True)
        source_path = settings.graph_instance_path
        if not source_path.exists():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Graph SQLite file not found")

        summary = self.runtime.get_graph_summary()
        timestamp = datetime.now(UTC)
        version = summary["current_version"] or timestamp.strftime("v%Y%m%d%H%M%S")
        filename = f"graph_{version}_{timestamp.strftime('%Y%m%d_%H%M%S')}.db"
        target_path = export_dir / filename
        shutil.copy2(source_path, target_path)

        session = get_graph_session_factory()()
        try:
            record = self.repo.create_sync_record(
                session,
                status="exported",
                started_at=timestamp,
                finished_at=timestamp,
                summary=f"Exported graph snapshot to {target_path}",
            )
            current_version = self.repo.get_current_version(session)
            if current_version is None:
                self.repo.replace_current_version(
                    session,
                    version=version,
                    exported_at=timestamp,
                    note=f"Exported to {target_path.name}",
                )
            session.commit()
        finally:
            session.close()

        latest = self.runtime.reload_graph()
        return {
            "record_id": record.id,
            "filename": target_path.name,
            "file_path": str(target_path),
            "download_url": f"/api/admin/graph/download/{quote(target_path.name)}",
            "version": version,
            **latest,
        }

    def import_graph_sqlite(self, upload: UploadFile) -> dict:
        import_dir = Path(settings.GRAPH_IMPORT_DIR).expanduser()
        import_dir.mkdir(parents=True, exist_ok=True)
        started_at = datetime.now(UTC)
        upload_name = Path(upload.filename or "graph_import.db").name
        staged_path = import_dir / f"staged_{upload_name}"
        instance_path = settings.graph_instance_path
        instance_path.parent.mkdir(parents=True, exist_ok=True)
        replacement_path = instance_path.with_suffix(instance_path.suffix + ".tmp")
        backup_path = instance_path.with_suffix(instance_path.suffix + ".bak")

        with staged_path.open("wb") as staged_file:
            shutil.copyfileobj(upload.file, staged_file)

        replaced = False
        try:
            self._validate_graph_sqlite(staged_path)
            if instance_path.exists():
                shutil.copy2(instance_path, backup_path)

            shutil.copy2(staged_path, replacement_path)
            os.replace(replacement_path, instance_path)
            replaced = True

            reset_graph_db_state()
            initialize_graph_database()
            self.runtime.reset()
            session = get_graph_session_factory()()
            try:
                version = started_at.strftime("import_%Y%m%d%H%M%S")
                record = self.repo.create_sync_record(
                    session,
                    status="imported",
                    started_at=started_at,
                    finished_at=datetime.now(UTC),
                    summary=f"Imported graph snapshot from {upload_name}",
                )
                self.repo.replace_current_version(
                    session,
                    version=version,
                    imported_at=datetime.now(UTC),
                    note=f"Imported from {upload_name}",
                )
                session.commit()
            finally:
                session.close()

            latest = self.runtime.reload_graph()
            return {
                "record_id": record.id,
                "filename": upload_name,
                "file_path": str(instance_path),
                "download_url": None,
                "version": version,
                **latest,
            }
        except GraphImportError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
        except Exception as exc:
            if replaced and backup_path.exists():
                os.replace(backup_path, instance_path)
                reset_graph_db_state()
                self.runtime.reset()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Graph import failed: {exc}") from exc
        finally:
            if staged_path.exists():
                staged_path.unlink()
            if replacement_path.exists():
                replacement_path.unlink()
            if backup_path.exists():
                backup_path.unlink()

    def resolve_export_download_path(self, filename: str) -> Path:
        export_dir = Path(settings.GRAPH_EXPORT_DIR).expanduser().resolve()
        file_path = (export_dir / filename).resolve()
        if file_path.parent != export_dir or not file_path.name.endswith(".db"):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid export filename")
        if not file_path.exists() or not file_path.is_file():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Export file not found")
        return file_path

    def list_nodes(
        self,
        *,
        limit: int,
        offset: int,
        node_type: str | None = None,
        keyword: str | None = None,
    ) -> dict:
        try:
            return self.runtime.list_nodes(limit=limit, offset=offset, node_type=node_type, keyword=keyword)
        except GraphUnavailableError as exc:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc

    def get_node_detail(self, *, node_id: str) -> dict:
        try:
            return {
                "node": self.runtime.get_node_detail(node_id),
            }
        except GraphNodeNotFoundError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Node not found") from exc
        except GraphUnavailableError as exc:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc

    def get_neighbors(self, *, node_id: str, limit: int) -> dict:
        try:
            safe_limit = min(limit, settings.GRAPH_MAX_NEIGHBORS)
            return self.runtime.get_neighbors(node_id, limit=safe_limit)
        except GraphNodeNotFoundError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Node not found") from exc
        except GraphUnavailableError as exc:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc

    def get_subgraph(self, *, node_id: str, depth: int, limit: int) -> dict:
        if depth < 1:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="depth must be >= 1")
        try:
            return self.runtime.get_subgraph(node_id, depth=depth, limit=limit)
        except GraphNodeNotFoundError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Node not found") from exc
        except GraphUnavailableError as exc:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc

    # Backward-compatible wrappers for the existing router/front-end.
    def get_overview(self, *, limit: int) -> dict:
        summary = self.get_summary()
        graph = self.runtime.get_subgraph_from_all(limit=limit) if hasattr(self.runtime, "get_subgraph_from_all") else None
        if graph is None:
            listing = self.list_nodes(limit=limit, offset=0)
            selected_ids = {node["id"] for node in listing["items"]}
            edges = self.runtime.get_edges_for_ids(selected_ids) if hasattr(self.runtime, "get_edges_for_ids") else []
            return {
                "nodes": listing["items"],
                "edges": edges,
                "total_nodes": summary["node_count"],
                "total_edges": summary["edge_count"],
            }
        return {
            "nodes": graph["nodes"],
            "edges": graph["edges"],
            "total_nodes": summary["node_count"],
            "total_edges": summary["edge_count"],
        }

    def get_node_details(self, *, node_id: str) -> dict:
        return self.get_node_detail(node_id=node_id)

    def get_hops(self, *, node_id: str, depth: int, limit: int) -> dict:
        return self.get_subgraph(node_id=node_id, depth=depth, limit=limit)

    def _validate_graph_sqlite(self, path: Path) -> None:
        try:
            with sqlite3.connect(path) as conn:
                tables = {
                    row[0]
                    for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()
                }
        except sqlite3.DatabaseError as exc:
            raise GraphImportError("Invalid SQLite file") from exc

        missing = sorted(_required_tables - tables)
        if missing:
            raise GraphImportError(f"Missing required graph tables: {', '.join(missing)}")

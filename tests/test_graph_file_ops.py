import asyncio
import io
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile
from sqlalchemy import text

from app.api.v1.admin_graph import clear_graph, download_graph_export, export_graph, import_graph
from app.api.v1.graph import graph_summary
from app.auth.principal import Principal
from app.core.config import settings
from app.db.session import get_session_factory, initialize_database, reset_db_state
from app.graph.db import get_graph_session_factory, initialize_graph_database, reset_graph_db_state
from app.models.document import Document
from app.models.graph_edge import GraphEdge
from app.models.graph_extraction_task import GraphExtractionTask
from app.models.graph_node import GraphNode
from app.services.runtime_status_service import runtime_status_service
from app.services.graph_service import _runtime


def _bootstrap(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(settings, "DIFY_BASE_URL", None)
    monkeypatch.setattr(settings, "DIFY_API_KEY", None)
    monkeypatch.setattr(settings, "DIFY_API_KEY_SECRET_NAME", None)
    monkeypatch.setattr(settings, "SQLITE_PATH", str(tmp_path / "app.db"))
    monkeypatch.setattr(settings, "DOCUMENT_LOCAL_STORAGE_DIR", str(tmp_path / "uploads"))
    monkeypatch.setattr(settings, "GRAPH_INSTANCE_LOCAL_PATH", str(tmp_path / "graph" / "runtime.db"))
    monkeypatch.setattr(settings, "GRAPH_EXPORT_DIR", str(tmp_path / "graph_exports"))
    monkeypatch.setattr(settings, "GRAPH_IMPORT_DIR", str(tmp_path / "graph_imports"))
    monkeypatch.setattr(settings, "GRAPH_ENABLED", True)
    reset_db_state()
    reset_graph_db_state()
    _runtime.reset()
    runtime_status_service.reset()
    initialize_database()
    initialize_graph_database()


def _admin_principal() -> Principal:
    return Principal(user_id=str(uuid4()), username="admin", roles=["admin"])


def _seed_runtime_graph() -> None:
    session = get_graph_session_factory()()
    now = datetime.now(UTC)
    try:
        session.add_all(
            [
                GraphNode(
                    id="n1",
                    name="Alice",
                    node_type="person",
                    source_document="doc-1",
                    description="Researcher",
                    tags_json='["alpha"]',
                    metadata_json="{}",
                    created_at=now,
                    updated_at=now,
                ),
                GraphNode(
                    id="n2",
                    name="AtlasCore",
                    node_type="system",
                    source_document="doc-2",
                    description="Backend",
                    tags_json="[]",
                    metadata_json="{}",
                    created_at=now,
                    updated_at=now,
                ),
            ]
        )
        session.add(
            GraphEdge(
                id="e1",
                source_id="n1",
                target_id="n2",
                relation_type="USES",
                relation_label="uses",
                source_document="doc-2",
                weight=1.0,
                metadata_json="{}",
                created_at=now,
                updated_at=now,
            )
        )
        session.commit()
    finally:
        session.close()


def _create_import_db(path: Path) -> None:
    now = datetime.now(UTC).isoformat()
    with sqlite3.connect(path) as conn:
        conn.executescript(
            """
            CREATE TABLE graph_nodes (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                node_type TEXT,
                source_document TEXT,
                description TEXT,
                tags_json TEXT,
                metadata_json TEXT,
                created_at TEXT,
                updated_at TEXT
            );
            CREATE TABLE graph_edges (
                id TEXT PRIMARY KEY,
                source_id TEXT NOT NULL,
                target_id TEXT NOT NULL,
                relation_type TEXT NOT NULL,
                relation_label TEXT,
                source_document TEXT,
                weight REAL,
                metadata_json TEXT,
                created_at TEXT,
                updated_at TEXT
            );
            CREATE TABLE graph_sync_records (
                id TEXT PRIMARY KEY,
                source_document_id TEXT,
                status TEXT NOT NULL,
                started_at TEXT NOT NULL,
                finished_at TEXT,
                error_message TEXT,
                summary TEXT
            );
            CREATE TABLE graph_versions (
                id TEXT PRIMARY KEY,
                version TEXT NOT NULL,
                build_time TEXT,
                source_batch TEXT,
                exported_at TEXT,
                imported_at TEXT,
                note TEXT,
                is_current INTEGER NOT NULL
            );
            """
        )
        conn.execute(
            """
            INSERT INTO graph_nodes (id, name, node_type, source_document, description, tags_json, metadata_json, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            ("x1", "Imported Node", "document", "seed", "from import", "[]", "{}", now, now),
        )
        conn.execute(
            """
            INSERT INTO graph_versions (id, version, imported_at, note, is_current)
            VALUES (?, ?, ?, ?, 1)
            """,
            (str(uuid4()), "seed-v1", now, "seed import"),
        )
        conn.commit()


def _seed_graph_assets(tmp_path: Path) -> None:
    now = datetime.now(UTC)
    uploads_dir = tmp_path / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)
    md_path = uploads_dir / "source.md"
    sqlite_path = uploads_dir / "snapshot.db"
    md_path.write_text("# AtlasCore", encoding="utf-8")
    sqlite_path.write_bytes(b"sqlite-bytes")

    session = get_session_factory()()
    try:
        session.add_all(
            [
                Document(
                    filename="source.md",
                    file_type="md",
                    source_type="upload",
                    status="applied_to_graph",
                    uploaded_at=now,
                    synced_to_dify=False,
                    synced_to_graph=True,
                    note="source",
                    local_path=str(md_path),
                    source_uri=str(md_path),
                    mime_type="text/markdown",
                    content_type="text/markdown",
                    file_size=10,
                    file_extension="md",
                    created_by=None,
                    created_at=now,
                ),
                Document(
                    filename="snapshot.db",
                    file_type="sqlite",
                    source_type="upload",
                    status="applied_to_graph",
                    uploaded_at=now,
                    synced_to_dify=False,
                    synced_to_graph=True,
                    note="snapshot",
                    local_path=str(sqlite_path),
                    source_uri=str(sqlite_path),
                    mime_type="application/octet-stream",
                    content_type="application/octet-stream",
                    file_size=12,
                    file_extension="db",
                    created_by=None,
                    created_at=now,
                ),
            ]
        )
        session.add(
            GraphExtractionTask(
                task_type="md_extraction",
                status="succeeded",
                selected_document_ids="[]",
                started_at=now,
                finished_at=now,
                result_summary="ok",
                output_graph_version="extract_seed",
                operator="admin",
            )
        )
        session.commit()
    finally:
        session.close()


def test_graph_export_generates_sqlite_snapshot(monkeypatch, tmp_path):
    _bootstrap(monkeypatch, tmp_path)
    _seed_runtime_graph()

    payload = export_graph(_=_admin_principal())
    download = download_graph_export(payload.filename, _=_admin_principal())

    assert payload.filename.endswith(".db")
    assert payload.node_count == 2
    assert Path(payload.file_path).exists()
    assert str(download.path) == payload.file_path
    status = asyncio.run(runtime_status_service.get_status())
    assert status["last_graph_export"]["filename"] == payload.filename


def test_graph_import_reloads_runtime(monkeypatch, tmp_path):
    _bootstrap(monkeypatch, tmp_path)
    _seed_runtime_graph()

    source_path = tmp_path / "incoming.db"
    _create_import_db(source_path)
    upload = UploadFile(filename="incoming.db", file=io.BytesIO(source_path.read_bytes()))

    payload = import_graph(_=_admin_principal(), file=upload)
    summary = graph_summary()

    assert payload.loaded is True
    assert payload.current_version is not None
    assert summary.node_count == 1
    assert summary.current_version == payload.current_version
    status = asyncio.run(runtime_status_service.get_status())
    assert status["last_graph_import"]["filename"] == "incoming.db"
    assert status["graph_loaded"] is True


def test_graph_import_rejects_invalid_file(monkeypatch, tmp_path):
    _bootstrap(monkeypatch, tmp_path)
    upload = UploadFile(filename="bad.db", file=io.BytesIO(b"not-a-sqlite-file"))

    try:
        import_graph(_=_admin_principal(), file=upload)
    except HTTPException as exc:
        assert exc.status_code == 400
        assert "Invalid SQLite file" in exc.detail
        status = asyncio.run(runtime_status_service.get_status())
        assert status["last_graph_import"]["status"] == "failed"
        assert status["last_error"]["error_type"] == "graph_import_error"
    else:
        raise AssertionError("Expected invalid graph SQLite import to be rejected")


def test_graph_clear_removes_runtime_and_assets(monkeypatch, tmp_path):
    _bootstrap(monkeypatch, tmp_path)
    _seed_runtime_graph()
    _seed_graph_assets(tmp_path)

    payload = clear_graph(current_admin=_admin_principal())
    summary = graph_summary()

    assert payload.cleared_scope == ["graph_sqlite_runtime", "graph_managed_files", "graph_extraction_tasks"]
    assert payload.deleted_document_count == 2
    assert payload.deleted_task_count == 1
    assert payload.deleted_file_count == 2
    assert payload.loaded is True
    assert payload.node_count == 0
    assert payload.edge_count == 0
    assert payload.current_version is None
    assert summary.node_count == 0
    assert summary.edge_count == 0
    assert summary.current_version is None

    graph_session = get_graph_session_factory()()
    try:
        assert graph_session.execute(text("SELECT COUNT(*) FROM graph_nodes")).scalar_one() == 0
        assert graph_session.execute(text("SELECT COUNT(*) FROM graph_edges")).scalar_one() == 0
        assert graph_session.execute(text("SELECT COUNT(*) FROM graph_node_sources")).scalar_one() == 0
        assert graph_session.execute(text("SELECT COUNT(*) FROM graph_sync_records")).scalar_one() == 0
        assert graph_session.execute(text("SELECT COUNT(*) FROM graph_versions")).scalar_one() == 0
    finally:
        graph_session.close()

    app_session = get_session_factory()()
    try:
        assert app_session.query(Document).count() == 0
        assert app_session.query(GraphExtractionTask).count() == 0
    finally:
        app_session.close()

    assert not (tmp_path / "uploads" / "source.md").exists()
    assert not (tmp_path / "uploads" / "snapshot.db").exists()
    status = asyncio.run(runtime_status_service.get_status())
    assert status["last_graph_import"]["status"] == "cleared"
    assert status["graph_loaded"] is True

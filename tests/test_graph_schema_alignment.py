from datetime import UTC, datetime

from sqlalchemy import text

from app.core.config import settings
from app.db.session import get_engine, initialize_database, reset_db_state
from app.graph.db import get_graph_engine, get_graph_session_factory, initialize_graph_database, reset_graph_db_state
from app.models.graph_node import GraphNode


def test_business_sqlite_alignment_adds_graph_extraction_fields(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "SQLITE_PATH", str(tmp_path / "app.db"))
    reset_db_state()
    initialize_database()

    with get_engine().begin() as connection:
        rows = connection.exec_driver_sql("PRAGMA table_info('documents')").fetchall()
        columns = {str(row[1]) for row in rows}

    assert "file_type" in columns
    assert "extraction_task_id" in columns
    assert "removed_from_graph_at" in columns
    assert "invalidated_at" in columns
    assert "is_active" in columns


def test_graph_sqlite_alignment_adds_node_source_ready_fields(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "GRAPH_INSTANCE_LOCAL_PATH", str(tmp_path / "graph.db"))
    reset_graph_db_state()
    initialize_graph_database()

    session = get_graph_session_factory()()
    now = datetime.now(UTC)
    try:
        session.add(
            GraphNode(
                id="n1",
                name="Alice Smith",
                normalized_name="",
                node_type="person",
                description="Researcher",
                tags_json="[]",
                metadata_json="{}",
                created_at=now,
                updated_at=now,
            )
        )
        session.commit()
    finally:
        session.close()

    reset_graph_db_state()
    initialize_graph_database()

    with get_graph_engine().begin() as connection:
        node_rows = connection.exec_driver_sql("PRAGMA table_info('graph_nodes')").fetchall()
        node_columns = {str(row[1]) for row in node_rows}
        edge_rows = connection.exec_driver_sql("PRAGMA table_info('graph_edges')").fetchall()
        edge_columns = {str(row[1]) for row in edge_rows}
        mapping_rows = connection.exec_driver_sql("PRAGMA table_info('graph_node_sources')").fetchall()
        normalized_name = connection.execute(text("SELECT normalized_name FROM graph_nodes WHERE id = 'n1'")).scalar_one()

    assert "normalized_name" in node_columns
    assert "source_document_id" in edge_columns
    assert {str(row[1]) for row in mapping_rows} >= {"id", "node_id", "document_id"}
    assert normalized_name == "alicesmith"

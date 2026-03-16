from datetime import UTC, datetime

from app.core.config import settings
from app.graph.db import get_graph_session_factory, initialize_graph_database, reset_graph_db_state
from app.models.graph_edge import GraphEdge
from app.models.graph_node import GraphNode
from app.repositories.graph_repo import GraphRepository


def _bootstrap_graph_db(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(settings, "GRAPH_INSTANCE_LOCAL_PATH", str(tmp_path / "graph" / "repo.db"))
    reset_graph_db_state()
    initialize_graph_database()


def test_graph_repo_queries_filters_and_version(monkeypatch, tmp_path):
    _bootstrap_graph_db(monkeypatch, tmp_path)
    repo = GraphRepository()
    session = get_graph_session_factory()()
    now = datetime.now(UTC)
    try:
        session.add_all(
            [
                GraphNode(
                    id="n1",
                    name="Alice",
                    node_type="person",
                    source_document="doc-a",
                    description="Researcher",
                    tags_json='["team-a"]',
                    metadata_json='{"level": 1}',
                    created_at=now,
                    updated_at=now,
                ),
                GraphNode(
                    id="n2",
                    name="Atlas",
                    node_type="system",
                    source_document="doc-b",
                    description="Platform",
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
                source_document="doc-a",
                weight=1.0,
                metadata_json="{}",
                created_at=now,
                updated_at=now,
            )
        )
        repo.replace_current_version(session, version="v1", imported_at=now, note="seed")
        session.commit()

        nodes, total = repo.list_nodes(session, limit=10, offset=0, node_type="person", keyword="Ali")
        assert total == 1
        assert nodes[0].id == "n1"

        assert len(repo.fetch_all_nodes(session)) == 2
        assert len(repo.fetch_all_edges(session)) == 1
        assert repo.get_current_version(session).version == "v1"
    finally:
        session.close()

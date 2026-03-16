from datetime import UTC, datetime
from uuid import uuid4

from app.api.v1.admin_graph import graph_status, reload_graph
from app.api.v1.graph import graph_overview, graph_summary, list_graph_nodes, node_details, node_neighbors, node_subgraph
from app.auth.principal import Principal
from app.core.config import settings
from app.graph.db import get_graph_session_factory, initialize_graph_database, reset_graph_db_state
from app.models.graph_edge import GraphEdge
from app.models.graph_node import GraphNode
from app.services.graph_service import _runtime


def _bootstrap(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(settings, "GRAPH_INSTANCE_LOCAL_PATH", str(tmp_path / "graph" / "api.db"))
    monkeypatch.setattr(settings, "GRAPH_EXPORT_DIR", str(tmp_path / "graph_exports"))
    monkeypatch.setattr(settings, "GRAPH_IMPORT_DIR", str(tmp_path / "graph_imports"))
    monkeypatch.setattr(settings, "GRAPH_ENABLED", True)
    reset_graph_db_state()
    _runtime.reset()
    initialize_graph_database()


def _seed_graph() -> None:
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


def _admin_principal() -> Principal:
    return Principal(user_id=str(uuid4()), username="admin", roles=["admin"])


def test_public_graph_routes(monkeypatch, tmp_path):
    _bootstrap(monkeypatch, tmp_path)
    _seed_graph()

    assert graph_summary().node_count == 2
    assert graph_overview(limit=10).total_edges == 1
    assert list_graph_nodes(limit=10, offset=0, node_type=None, keyword="Ali").total == 1
    assert node_details("n1").node.id == "n1"
    assert node_neighbors("n1", limit=10).center_node_id == "n1"
    assert node_subgraph("n1", depth=1, limit=10).center_node_id == "n1"


def test_admin_graph_routes(monkeypatch, tmp_path):
    _bootstrap(monkeypatch, tmp_path)
    _seed_graph()

    status_payload = graph_status(_=_admin_principal())
    reload_payload = reload_graph(_=_admin_principal())

    assert status_payload.enabled is True
    assert status_payload.instance_local_path.endswith("api.db")
    assert reload_payload.loaded is True
    assert reload_payload.node_count == 2

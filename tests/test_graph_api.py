from datetime import UTC, datetime
from uuid import uuid4

from app.api.v1.admin_graph import graph_status, reload_graph
from app.api.v1.graph import graph_overview, graph_summary, list_graph_nodes, node_details, node_neighbors, node_subgraph
from app.auth.principal import Principal
from app.core.config import settings
from app.db.session import get_session_factory, initialize_database, reset_db_state
from app.graph.db import get_graph_session_factory, initialize_graph_database, reset_graph_db_state
from app.models.document import Document
from app.models.graph_edge import GraphEdge
from app.models.graph_node import GraphNode
from app.models.graph_node_source import GraphNodeSource
from app.services.graph_service import _runtime


def _bootstrap(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(settings, "GRAPH_INSTANCE_LOCAL_PATH", str(tmp_path / "graph" / "api.db"))
    monkeypatch.setattr(settings, "SQLITE_PATH", str(tmp_path / "app.db"))
    monkeypatch.setattr(settings, "GRAPH_EXPORT_DIR", str(tmp_path / "graph_exports"))
    monkeypatch.setattr(settings, "GRAPH_IMPORT_DIR", str(tmp_path / "graph_imports"))
    monkeypatch.setattr(settings, "GRAPH_INSTANCE_ID", "api-instance")
    monkeypatch.setattr(settings, "GRAPH_DB_VERSION", "api-v1")
    monkeypatch.setattr(settings, "GRAPH_ENABLED", True)
    reset_db_state()
    reset_graph_db_state()
    _runtime.reset()
    initialize_database()
    initialize_graph_database()


def _seed_graph() -> None:
    business_session = get_session_factory()()
    document_id = uuid4()
    session = get_graph_session_factory()()
    now = datetime.now(UTC)
    try:
        business_session.add(
            Document(
                id=document_id,
                filename="people.md",
                file_type="md",
                source_type="manual",
                status="synced",
                uploaded_at=now,
                synced_to_dify=False,
                synced_to_graph=True,
                note=None,
                local_path=None,
                source_uri=None,
                mime_type="text/markdown",
                content_type="text/markdown",
                file_size=10,
                file_extension="md",
                created_by=None,
                created_at=now,
            )
        )
        business_session.commit()
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
            GraphNodeSource(
                id="ns1",
                node_id="n1",
                document_id=str(document_id),
                source_ref=None,
                created_at=now,
                updated_at=now,
            )
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
        business_session.close()
        session.close()


def _admin_principal() -> Principal:
    return Principal(user_id=str(uuid4()), username="admin", roles=["admin"])


def test_public_graph_routes(monkeypatch, tmp_path):
    _bootstrap(monkeypatch, tmp_path)
    _seed_graph()

    assert graph_summary().node_count == 2
    overview = graph_overview(limit=10)
    assert overview.total_edges == 1
    assert overview.metadata["query"] == "overview"
    assert list_graph_nodes(limit=10, offset=0, node_type=None, keyword="Ali").total == 1
    detail = node_details("n1")
    assert detail.node.id == "n1"
    assert detail.detail is not None
    assert detail.description == "Researcher"
    assert detail.source_documents[0].title == "people.md"
    assert detail.related_entities[0].id == "n2"
    assert detail.metadata["query"] == "node_detail"
    neighbors = node_neighbors("n1", limit=10)
    assert neighbors.center_node_id == "n1"
    assert neighbors.metadata["query"] == "neighbors"
    subgraph = node_subgraph("n1", depth=1, limit=10)
    assert subgraph.center_node_id == "n1"
    assert subgraph.metadata["query"] == "subgraph"


def test_admin_graph_routes(monkeypatch, tmp_path):
    _bootstrap(monkeypatch, tmp_path)
    _seed_graph()

    status_payload = graph_status(_=_admin_principal())
    reload_payload = reload_graph(_=_admin_principal())

    assert status_payload.enabled is True
    assert status_payload.instance_id == "api-instance"
    assert status_payload.graph_db_version == "api-v1"
    assert status_payload.instance_local_path.endswith("api.db")
    assert status_payload.instance_local_path_exists is True
    assert status_payload.multi_instance_mode == "instance_local_sqlite_only"
    assert reload_payload.loaded is True
    assert reload_payload.node_count == 2

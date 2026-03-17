from datetime import UTC, datetime
from uuid import uuid4

from fastapi import HTTPException

from app.core.config import settings
from app.db.session import get_session_factory, initialize_database, reset_db_state
from app.graph.db import get_graph_session_factory, initialize_graph_database, reset_graph_db_state
from app.models.document import Document
from app.graph.graph_loader import GraphLoader
from app.graph.graph_runtime import GraphRuntime
from app.models.graph_edge import GraphEdge
from app.models.graph_node import GraphNode
from app.models.graph_node_source import GraphNodeSource
from app.services.graph_service import GraphService


def _seed_graph(monkeypatch, tmp_path) -> GraphService:
    monkeypatch.setattr(settings, "GRAPH_INSTANCE_LOCAL_PATH", str(tmp_path / "graph" / "service.db"))
    monkeypatch.setattr(settings, "SQLITE_PATH", str(tmp_path / "app.db"))
    monkeypatch.setattr(settings, "GRAPH_ENABLED", True)
    monkeypatch.setattr(settings, "GRAPH_MAX_NEIGHBORS", 2)
    reset_db_state()
    reset_graph_db_state()
    initialize_database()
    initialize_graph_database()

    business_session = get_session_factory()()
    primary_doc_id = uuid4()
    now = datetime.now(UTC)
    try:
        business_session.add_all(
            [
                Document(
                    id=primary_doc_id,
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
                ),
            ]
        )
        business_session.commit()
    finally:
        business_session.close()

    session = get_graph_session_factory()()
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
                    metadata_json='{"score": 10}',
                    created_at=now,
                    updated_at=now,
                ),
                GraphNode(
                    id="n2",
                    name="Bob",
                    node_type="person",
                    source_document="doc-1",
                    description="Engineer",
                    tags_json='["beta"]',
                    metadata_json="{}",
                    created_at=now,
                    updated_at=now,
                ),
                GraphNode(
                    id="n3",
                    name="AtlasCore",
                    node_type="system",
                    source_document="system.md",
                    description=None,
                    tags_json="[]",
                    metadata_json="{}",
                    created_at=now,
                    updated_at=now,
                ),
            ]
        )
        session.add_all(
            [
                GraphEdge(
                    id="e1",
                    source_id="n1",
                    target_id="n2",
                    relation_type="KNOWS",
                    relation_label="knows",
                    source_document="doc-1",
                    weight=0.8,
                    metadata_json="{}",
                    created_at=now,
                    updated_at=now,
                ),
                GraphEdge(
                    id="e2",
                    source_id="n2",
                    target_id="n3",
                    relation_type="USES",
                    relation_label="uses",
                    source_document="doc-2",
                    weight=1.0,
                    metadata_json="{}",
                    created_at=now,
                    updated_at=now,
                ),
            ]
        )
        session.add_all(
            [
                GraphNodeSource(
                    id="ns1",
                    node_id="n1",
                    document_id=str(primary_doc_id),
                    source_ref=None,
                    created_at=now,
                    updated_at=now,
                ),
                GraphNodeSource(
                    id="ns2",
                    node_id="n2",
                    document_id=str(primary_doc_id),
                    source_ref=None,
                    created_at=now,
                    updated_at=now,
                ),
            ]
        )
        session.commit()
    finally:
        session.close()

    runtime = GraphRuntime(loader=GraphLoader())
    return GraphService(runtime=runtime)


def test_get_overview_and_summary(monkeypatch, tmp_path):
    service = _seed_graph(monkeypatch, tmp_path)

    payload = service.get_overview(limit=10)
    summary = service.get_summary()

    assert payload["total_nodes"] == 3
    assert payload["total_edges"] == 2
    assert len(payload["nodes"]) == 3
    assert summary["loaded"] is True
    assert summary["node_count"] == 3


def test_list_nodes_filters(monkeypatch, tmp_path):
    service = _seed_graph(monkeypatch, tmp_path)

    payload = service.list_nodes(limit=10, offset=0, node_type="person", keyword="Ali")

    assert payload["total"] == 1
    assert payload["items"][0]["id"] == "n1"


def test_get_node_detail(monkeypatch, tmp_path):
    service = _seed_graph(monkeypatch, tmp_path)

    payload = service.get_node_detail(node_id="n1")

    assert payload["node"]["id"] == "n1"
    assert payload["node"]["properties"]["name"] == "Alice"
    assert payload["description"] == "Researcher"
    assert len(payload["source_documents"]) == 1
    assert payload["source_documents"][0]["title"] == "people.md"
    assert payload["source_documents"][0]["document_id"] is not None
    assert payload["related_entities"] == [{"id": "n2", "name": "Bob", "node_type": "person", "labels": ["person"]}]


def test_get_node_detail_gracefully_handles_missing_description_and_source(monkeypatch, tmp_path):
    service = _seed_graph(monkeypatch, tmp_path)

    payload = service.get_node_detail(node_id="n3")

    assert payload["description"] is None
    assert payload["source_documents"] == [{"document_id": None, "title": "system.md"}]
    assert payload["related_entities"] == [{"id": "n2", "name": "Bob", "node_type": "person", "labels": ["person"]}]


def test_get_neighbors(monkeypatch, tmp_path):
    service = _seed_graph(monkeypatch, tmp_path)

    payload = service.get_neighbors(node_id="n2", limit=10)

    assert payload["center_node_id"] == "n2"
    assert {node["id"] for node in payload["nodes"]} == {"n1", "n2", "n3"}
    assert len(payload["edges"]) == 2


def test_get_subgraph(monkeypatch, tmp_path):
    service = _seed_graph(monkeypatch, tmp_path)

    payload = service.get_subgraph(node_id="n1", depth=2, limit=10)

    assert payload["center_node_id"] == "n1"
    assert payload["depth"] == 2
    assert {node["id"] for node in payload["nodes"]} == {"n1", "n2", "n3"}


def test_missing_node_returns_404(monkeypatch, tmp_path):
    service = _seed_graph(monkeypatch, tmp_path)

    try:
        service.get_node_detail(node_id="missing")
    except HTTPException as exc:
        assert exc.status_code == 404
    else:
        raise AssertionError("Expected 404 for missing node")

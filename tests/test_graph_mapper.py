from datetime import UTC, datetime

from app.graph.mapper import map_edge_record, map_graph_records, map_node_record
from app.models.graph_edge import GraphEdge
from app.models.graph_node import GraphNode


def test_graph_mapper_maps_sqlite_records():
    now = datetime.now(UTC)
    node = GraphNode(
        id="n1",
        name="Alice",
        node_type="person",
        source_document="doc-1",
        description="Researcher",
        tags_json='["alpha"]',
        metadata_json='{"score": 1}',
        created_at=now,
        updated_at=now,
    )
    edge = GraphEdge(
        id="e1",
        source_id="n1",
        target_id="n2",
        relation_type="KNOWS",
        relation_label="knows",
        source_document="doc-1",
        weight=0.6,
        metadata_json='{"confidence": 0.6}',
        created_at=now,
        updated_at=now,
    )

    mapped_node = map_node_record(node)
    mapped_edge = map_edge_record(edge)
    mapped_graph = map_graph_records([node], [edge])

    assert mapped_node["labels"] == ["person"]
    assert mapped_node["properties"]["tags"] == ["alpha"]
    assert mapped_edge["type"] == "KNOWS"
    assert mapped_graph["nodes"][0]["id"] == "n1"
    assert mapped_graph["edges"][0]["id"] == "e1"

import json
from typing import Any

from app.models.graph_edge import GraphEdge
from app.models.graph_node import GraphNode


def _parse_json(value: str | None, fallback: Any) -> Any:
    if not value:
        return fallback
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return fallback


def map_node_record(node: GraphNode) -> dict[str, Any]:
    metadata = _parse_json(node.metadata_json, {})
    tags = _parse_json(node.tags_json, [])
    properties = {
        "name": node.name,
        "node_type": node.node_type,
        "source_document": node.source_document,
        "description": node.description,
        "tags": tags,
        "metadata": metadata,
        "created_at": node.created_at.isoformat(),
        "updated_at": node.updated_at.isoformat(),
    }
    return {
        "id": node.id,
        "labels": [node.node_type] if node.node_type else [],
        "properties": properties,
        "detail": properties,
    }


def map_edge_record(edge: GraphEdge) -> dict[str, Any]:
    metadata = _parse_json(edge.metadata_json, {})
    properties = {
        "relation_label": edge.relation_label,
        "source_document": edge.source_document,
        "weight": edge.weight,
        "metadata": metadata,
        "created_at": edge.created_at.isoformat(),
        "updated_at": edge.updated_at.isoformat(),
    }
    return {
        "id": edge.id,
        "type": edge.relation_type,
        "source": edge.source_id,
        "target": edge.target_id,
        "properties": properties,
    }


def map_graph_records(nodes: list[GraphNode], edges: list[GraphEdge]) -> dict[str, list[dict[str, Any]]]:
    return {
        "nodes": [map_node_record(node) for node in nodes],
        "edges": [map_edge_record(edge) for edge in edges],
    }

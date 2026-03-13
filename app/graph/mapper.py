from typing import Any


def _node_id(node: Any) -> str:
    # element_id is available in Neo4j v5 driver objects.
    return str(getattr(node, "element_id", getattr(node, "id", "")))


def _rel_id(rel: Any) -> str:
    return str(getattr(rel, "element_id", getattr(rel, "id", "")))


def map_node(node: Any) -> dict[str, Any]:
    return {
        "id": _node_id(node),
        "labels": list(getattr(node, "labels", [])),
        "properties": dict(node),
    }


def map_edge(rel: Any) -> dict[str, Any]:
    start_id = str(getattr(rel, "start_node_element_id", getattr(rel, "start_node", "")))
    end_id = str(getattr(rel, "end_node_element_id", getattr(rel, "end_node", "")))
    if not isinstance(start_id, str):
        start_id = str(start_id)
    if not isinstance(end_id, str):
        end_id = str(end_id)

    return {
        "id": _rel_id(rel),
        "type": str(getattr(rel, "type", "")),
        "source": start_id,
        "target": end_id,
        "properties": dict(rel),
    }


def map_records_to_graph(records: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    node_map: dict[str, dict[str, Any]] = {}
    edge_map: dict[str, dict[str, Any]] = {}

    for item in records:
        for value in item.values():
            if hasattr(value, "labels"):
                mapped = map_node(value)
                node_map[mapped["id"]] = mapped
            elif hasattr(value, "type") and hasattr(value, "start_node_element_id"):
                mapped = map_edge(value)
                edge_map[mapped["id"]] = mapped

    return {"nodes": list(node_map.values()), "edges": list(edge_map.values())}

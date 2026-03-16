from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from threading import RLock

import networkx as nx

from app.core.config import settings
from app.graph.exceptions import GraphNodeNotFoundError, GraphUnavailableError
from app.graph.graph_loader import GraphDataBundle, GraphLoader
from app.graph.graph_mapper import map_edge_record, map_node_record
from app.models.graph_edge import GraphEdge
from app.models.graph_node import GraphNode


@dataclass(slots=True)
class GraphState:
    graph: nx.MultiDiGraph
    loaded_at: datetime
    current_version: str | None
    sqlite_path: str


class GraphRuntime:
    def __init__(self, loader: GraphLoader | None = None) -> None:
        self.loader = loader or GraphLoader()
        self._lock = RLock()
        self._state: GraphState | None = None

    def load_graph(self, force: bool = False) -> dict:
        if not settings.GRAPH_ENABLED:
            raise GraphUnavailableError("Graph module is disabled")

        with self._lock:
            if self._state is not None and self._state.sqlite_path == str(settings.graph_instance_path) and not force:
                return self.get_graph_summary()

            bundle = self.loader.load()
            self._state = GraphState(
                graph=self._build_graph(bundle),
                loaded_at=datetime.now(UTC),
                current_version=bundle.current_version,
                sqlite_path=str(settings.graph_instance_path),
            )
            return self.get_graph_summary()

    def reload_graph(self) -> dict:
        return self.load_graph(force=True)

    def ensure_loaded(self) -> GraphState:
        if self._state is None:
            self.load_graph()
        if self._state is None:
            raise GraphUnavailableError("Graph state is unavailable")
        return self._state

    def reset(self) -> None:
        with self._lock:
            self._state = None

    def get_graph_summary(self) -> dict:
        state = self._state
        return {
            "loaded": state is not None,
            "node_count": state.graph.number_of_nodes() if state else 0,
            "edge_count": state.graph.number_of_edges() if state else 0,
            "current_version": state.current_version if state else None,
            "sqlite_path": str(settings.graph_instance_path),
            "last_loaded_at": state.loaded_at if state else None,
        }

    def list_nodes(
        self,
        *,
        limit: int,
        offset: int,
        node_type: str | None = None,
        keyword: str | None = None,
    ) -> dict:
        state = self.ensure_loaded()
        items = [self._node_from_graph(node_id) for node_id in state.graph.nodes]
        if node_type:
            items = [item for item in items if item.node_type == node_type]
        if keyword:
            normalized = keyword.strip().lower()
            items = [
                item
                for item in items
                if normalized in item.id.lower()
                or normalized in item.name.lower()
                or normalized in (item.description or "").lower()
                or normalized in (item.source_document or "").lower()
            ]

        items.sort(key=lambda item: (item.name.lower(), item.id))
        total = len(items)
        selected = items[offset : offset + limit]
        return {
            "items": [map_node_record(item) for item in selected],
            "total": total,
            "limit": limit,
            "offset": offset,
        }

    def get_node_detail(self, node_id: str) -> dict:
        node = self._node_from_graph(node_id)
        return map_node_record(node)

    def get_subgraph_from_all(self, *, limit: int) -> dict:
        state = self.ensure_loaded()
        selected_ids = sorted(state.graph.nodes)[:limit]
        node_ids = set(selected_ids)
        edges = self._edges_for_node_set(node_ids)
        return {
            "nodes": [map_node_record(self._node_from_graph(item_id)) for item_id in selected_ids],
            "edges": [map_edge_record(edge) for edge in edges],
        }

    def get_edges_for_ids(self, node_ids: set[str]) -> list[dict]:
        return [map_edge_record(edge) for edge in self._edges_for_node_set(node_ids)]

    def get_neighbors(self, node_id: str, *, limit: int) -> dict:
        state = self.ensure_loaded()
        if node_id not in state.graph:
            raise GraphNodeNotFoundError(node_id)

        neighbor_ids: list[str] = []
        seen = set()
        for source_id, target_id, _key in state.graph.out_edges(node_id, keys=True):
            candidate = target_id if source_id == node_id else source_id
            if candidate not in seen:
                seen.add(candidate)
                neighbor_ids.append(candidate)
        for source_id, target_id, _key in state.graph.in_edges(node_id, keys=True):
            candidate = source_id if target_id == node_id else target_id
            if candidate not in seen:
                seen.add(candidate)
                neighbor_ids.append(candidate)

        neighbor_ids = neighbor_ids[:limit]
        node_ids = {node_id, *neighbor_ids}
        edges = self._edges_for_node_set(node_ids)
        return {
            "center_node_id": node_id,
            "center": map_node_record(self._node_from_graph(node_id)),
            "nodes": [map_node_record(self._node_from_graph(item_id)) for item_id in [node_id, *neighbor_ids]],
            "edges": [map_edge_record(edge) for edge in edges],
        }

    def get_subgraph(self, node_id: str, *, depth: int = 1, limit: int = 200) -> dict:
        state = self.ensure_loaded()
        if node_id not in state.graph:
            raise GraphNodeNotFoundError(node_id)

        undirected = state.graph.to_undirected()
        lengths = nx.single_source_shortest_path_length(undirected, node_id, cutoff=max(depth, 1))
        selected_ids = [item_id for item_id, _distance in sorted(lengths.items(), key=lambda item: (item[1], item[0]))][:limit]
        node_ids = set(selected_ids)
        edges = self._edges_for_node_set(node_ids)
        return {
            "center_node_id": node_id,
            "depth": depth,
            "center": map_node_record(self._node_from_graph(node_id)),
            "nodes": [map_node_record(self._node_from_graph(item_id)) for item_id in selected_ids],
            "edges": [map_edge_record(edge) for edge in edges],
            "detail": map_node_record(self._node_from_graph(node_id)),
        }

    def _build_graph(self, bundle: GraphDataBundle) -> nx.MultiDiGraph:
        graph = nx.MultiDiGraph()
        for node in bundle.nodes:
            graph.add_node(node.id, record=node)
        for edge in bundle.edges:
            if edge.source_id not in graph:
                graph.add_node(edge.source_id, record=self._placeholder_node(edge.source_id))
            if edge.target_id not in graph:
                graph.add_node(edge.target_id, record=self._placeholder_node(edge.target_id))
            graph.add_edge(edge.source_id, edge.target_id, key=edge.id, record=edge)
        return graph

    def _node_from_graph(self, node_id: str) -> GraphNode:
        state = self.ensure_loaded()
        if node_id not in state.graph:
            raise GraphNodeNotFoundError(node_id)
        node = state.graph.nodes[node_id]["record"]
        if not isinstance(node, GraphNode):
            raise GraphNodeNotFoundError(node_id)
        return node

    def _edges_for_node_set(self, node_ids: set[str]) -> list[GraphEdge]:
        state = self.ensure_loaded()
        edges: list[GraphEdge] = []
        for source_id, target_id, _key, data in state.graph.edges(keys=True, data=True):
            if source_id in node_ids and target_id in node_ids:
                edge = data["record"]
                if isinstance(edge, GraphEdge):
                    edges.append(edge)
        edges.sort(key=lambda item: item.id)
        return edges

    @staticmethod
    def _placeholder_node(node_id: str) -> GraphNode:
        now = datetime.now(UTC)
        return GraphNode(
            id=node_id,
            name=node_id,
            node_type="unknown",
            source_document=None,
            description=None,
            tags_json="[]",
            metadata_json="{}",
            created_at=now,
            updated_at=now,
        )

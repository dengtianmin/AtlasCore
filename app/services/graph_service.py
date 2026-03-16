from fastapi import HTTPException, status

from app.core.config import settings
from app.graph.exceptions import GraphNodeNotFoundError, GraphUnavailableError
from app.graph.graph_runtime import GraphRuntime

_runtime = GraphRuntime()


class GraphService:
    def __init__(self, runtime: GraphRuntime | None = None) -> None:
        self.runtime = runtime or _runtime

    def get_summary(self) -> dict:
        try:
            return self.runtime.load_graph()
        except GraphUnavailableError as exc:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc

    def list_nodes(
        self,
        *,
        limit: int,
        offset: int,
        node_type: str | None = None,
        keyword: str | None = None,
    ) -> dict:
        try:
            return self.runtime.list_nodes(limit=limit, offset=offset, node_type=node_type, keyword=keyword)
        except GraphUnavailableError as exc:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc

    def get_node_detail(self, *, node_id: str) -> dict:
        try:
            return {
                "node": self.runtime.get_node_detail(node_id),
            }
        except GraphNodeNotFoundError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Node not found") from exc
        except GraphUnavailableError as exc:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc

    def get_neighbors(self, *, node_id: str, limit: int) -> dict:
        try:
            safe_limit = min(limit, settings.GRAPH_MAX_NEIGHBORS)
            return self.runtime.get_neighbors(node_id, limit=safe_limit)
        except GraphNodeNotFoundError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Node not found") from exc
        except GraphUnavailableError as exc:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc

    def get_subgraph(self, *, node_id: str, depth: int, limit: int) -> dict:
        if depth < 1:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="depth must be >= 1")
        try:
            return self.runtime.get_subgraph(node_id, depth=depth, limit=limit)
        except GraphNodeNotFoundError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Node not found") from exc
        except GraphUnavailableError as exc:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc

    # Backward-compatible wrappers for the existing router/front-end.
    def get_overview(self, *, limit: int) -> dict:
        summary = self.get_summary()
        graph = self.runtime.get_subgraph_from_all(limit=limit) if hasattr(self.runtime, "get_subgraph_from_all") else None
        if graph is None:
            listing = self.list_nodes(limit=limit, offset=0)
            selected_ids = {node["id"] for node in listing["items"]}
            edges = self.runtime.get_edges_for_ids(selected_ids) if hasattr(self.runtime, "get_edges_for_ids") else []
            return {
                "nodes": listing["items"],
                "edges": edges,
                "total_nodes": summary["node_count"],
                "total_edges": summary["edge_count"],
            }
        return {
            "nodes": graph["nodes"],
            "edges": graph["edges"],
            "total_nodes": summary["node_count"],
            "total_edges": summary["edge_count"],
        }

    def get_node_details(self, *, node_id: str) -> dict:
        return self.get_node_detail(node_id=node_id)

    def get_hops(self, *, node_id: str, depth: int, limit: int) -> dict:
        return self.get_subgraph(node_id=node_id, depth=depth, limit=limit)

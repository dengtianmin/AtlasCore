from fastapi import HTTPException, status

from app.graph.exceptions import GraphQueryError, GraphUnavailableError
from app.graph.mapper import map_records_to_graph
from app.repositories.graph_repo import GraphRepository


class GraphService:
    def __init__(self, repo: GraphRepository | None = None) -> None:
        self.repo = repo

    def get_overview(self, *, limit: int) -> dict:
        repo = self._get_repo()
        records = self._safe_query(repo.fetch_overview, limit=limit)
        graph = map_records_to_graph(records)
        return {
            **graph,
            "total_nodes": len(graph["nodes"]),
            "total_edges": len(graph["edges"]),
        }

    def get_node_details(self, *, node_id: str) -> dict:
        repo = self._get_repo()
        records = self._safe_query(repo.fetch_node, node_id=node_id)
        graph = map_records_to_graph(records)
        if not graph["nodes"]:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Node not found")
        return {"node": graph["nodes"][0]}

    def get_neighbors(self, *, node_id: str, limit: int) -> dict:
        repo = self._get_repo()
        records = self._safe_query(repo.fetch_neighbors, node_id=node_id, limit=limit)
        graph = map_records_to_graph(records)
        if not graph["nodes"]:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Node not found")
        return {"center_node_id": node_id, **graph}

    def get_hops(self, *, node_id: str, depth: int, limit: int) -> dict:
        if depth not in {1, 2}:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="depth must be 1 or 2")
        repo = self._get_repo()
        records = self._safe_query(repo.fetch_hops, node_id=node_id, depth=depth, limit=limit)
        graph = map_records_to_graph(records)
        if not graph["nodes"]:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Node not found")
        return {"center_node_id": node_id, "depth": depth, **graph}

    def _safe_query(self, fn, **kwargs):
        try:
            return fn(**kwargs)
        except GraphUnavailableError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Graph backend unavailable: {exc}",
            ) from exc
        except GraphQueryError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=str(exc),
            ) from exc

    def _get_repo(self) -> GraphRepository:
        try:
            return self.repo or GraphRepository()
        except GraphUnavailableError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Graph backend unavailable: {exc}",
            ) from exc

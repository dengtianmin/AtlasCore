from dataclasses import dataclass

from app.graph.db import get_graph_session_factory
from app.models.graph_edge import GraphEdge
from app.models.graph_node import GraphNode
from app.repositories.graph_repo import GraphRepository


@dataclass(slots=True)
class GraphDataBundle:
    nodes: list[GraphNode]
    edges: list[GraphEdge]
    current_version: str | None


class GraphLoader:
    def __init__(self, repo: GraphRepository | None = None) -> None:
        self.repo = repo or GraphRepository()
        self._session_factory = get_graph_session_factory

    def load(self) -> GraphDataBundle:
        session = self._session_factory()()
        try:
            nodes = self.repo.fetch_all_nodes(session)
            edges = self.repo.fetch_all_edges(session)
            version = self.repo.get_current_version(session)
            return GraphDataBundle(
                nodes=nodes,
                edges=edges,
                current_version=version.version if version else None,
            )
        finally:
            session.close()

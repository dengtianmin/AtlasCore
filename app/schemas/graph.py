from typing import Any

from pydantic import BaseModel


class GraphNode(BaseModel):
    id: str
    labels: list[str]
    properties: dict[str, Any]


class GraphEdge(BaseModel):
    id: str
    type: str
    source: str
    target: str
    properties: dict[str, Any]


class GraphDataResponse(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]


class GraphOverviewResponse(GraphDataResponse):
    total_nodes: int
    total_edges: int


class NodeDetailsResponse(BaseModel):
    node: GraphNode


class NodeNeighborsResponse(GraphDataResponse):
    center_node_id: str


class NodeHopsResponse(GraphDataResponse):
    center_node_id: str
    depth: int

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class GraphNode(BaseModel):
    id: str
    labels: list[str]
    properties: dict[str, Any]
    detail: dict[str, Any] | None = None


class GraphEdge(BaseModel):
    id: str
    type: str
    source: str
    target: str
    properties: dict[str, Any]


class GraphDataResponse(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]
    center: GraphNode | None = None
    detail: GraphNode | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class GraphOverviewResponse(GraphDataResponse):
    total_nodes: int
    total_edges: int


class GraphSummaryResponse(BaseModel):
    loaded: bool
    node_count: int
    edge_count: int
    current_version: str | None
    sqlite_path: str
    last_loaded_at: datetime | None


class GraphNodeListResponse(BaseModel):
    items: list[GraphNode]
    total: int
    limit: int
    offset: int


class NodeDetailsResponse(BaseModel):
    node: GraphNode
    detail: GraphNode | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class NodeNeighborsResponse(GraphDataResponse):
    center_node_id: str


class NodeHopsResponse(GraphDataResponse):
    center_node_id: str
    depth: int

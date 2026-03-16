from fastapi import APIRouter, Query

from app.core.config import settings
from app.schemas.graph import (
    GraphNodeListResponse,
    GraphOverviewResponse,
    GraphSummaryResponse,
    NodeDetailsResponse,
    NodeHopsResponse,
    NodeNeighborsResponse,
)
from app.services.graph_service import GraphService

router = APIRouter(prefix="/graph", tags=["graph"])
service = GraphService()


@router.get("/summary", response_model=GraphSummaryResponse)
def graph_summary() -> GraphSummaryResponse:
    return GraphSummaryResponse(**service.get_summary())


@router.get("/overview", response_model=GraphOverviewResponse)
def graph_overview(
    limit: int = Query(default=settings.GRAPH_DEFAULT_LIMIT, ge=1, le=1000),
) -> GraphOverviewResponse:
    return GraphOverviewResponse(**service.get_overview(limit=limit))


@router.get("/nodes", response_model=GraphNodeListResponse)
def list_graph_nodes(
    limit: int = Query(default=settings.GRAPH_DEFAULT_LIMIT, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    node_type: str | None = Query(default=None),
    keyword: str | None = Query(default=None),
) -> GraphNodeListResponse:
    return GraphNodeListResponse(**service.list_nodes(limit=limit, offset=offset, node_type=node_type, keyword=keyword))


@router.get("/nodes/{node_id}", response_model=NodeDetailsResponse)
def node_details(node_id: str) -> NodeDetailsResponse:
    return NodeDetailsResponse(**service.get_node_detail(node_id=node_id))


@router.get("/nodes/{node_id}/neighbors", response_model=NodeNeighborsResponse)
def node_neighbors(
    node_id: str,
    limit: int = Query(default=settings.GRAPH_MAX_NEIGHBORS, ge=1, le=5000),
) -> NodeNeighborsResponse:
    return NodeNeighborsResponse(**service.get_neighbors(node_id=node_id, limit=limit))


@router.get("/subgraph/{node_id}", response_model=NodeHopsResponse)
def node_subgraph(
    node_id: str,
    depth: int = Query(default=1, ge=1, le=3),
    limit: int = Query(default=200, ge=1, le=2000),
) -> NodeHopsResponse:
    return NodeHopsResponse(**service.get_subgraph(node_id=node_id, depth=depth, limit=limit))


@router.get("/nodes/{node_id}/hops", response_model=NodeHopsResponse)
def node_hops(
    node_id: str,
    depth: int = Query(default=1, ge=1, le=3),
    limit: int = Query(default=200, ge=1, le=2000),
) -> NodeHopsResponse:
    return NodeHopsResponse(**service.get_hops(node_id=node_id, depth=depth, limit=limit))

from fastapi import APIRouter, Query
from app.schemas.graph import (
    GraphOverviewResponse,
    NodeDetailsResponse,
    NodeHopsResponse,
    NodeNeighborsResponse,
)
from app.services.graph_service import GraphService

router = APIRouter(prefix="/graph", tags=["graph"])
service = GraphService()


@router.get("/overview", response_model=GraphOverviewResponse)
def graph_overview(
    limit: int = Query(default=100, ge=1, le=500),
) -> GraphOverviewResponse:
    return GraphOverviewResponse(**service.get_overview(limit=limit))


@router.get("/nodes/{node_id}", response_model=NodeDetailsResponse)
def node_details(
    node_id: str,
) -> NodeDetailsResponse:
    return NodeDetailsResponse(**service.get_node_details(node_id=node_id))


@router.get("/nodes/{node_id}/neighbors", response_model=NodeNeighborsResponse)
def node_neighbors(
    node_id: str,
    limit: int = Query(default=100, ge=1, le=500),
) -> NodeNeighborsResponse:
    return NodeNeighborsResponse(**service.get_neighbors(node_id=node_id, limit=limit))


@router.get("/nodes/{node_id}/hops", response_model=NodeHopsResponse)
def node_hops(
    node_id: str,
    depth: int = Query(default=1, ge=1, le=2),
    limit: int = Query(default=200, ge=1, le=1000),
) -> NodeHopsResponse:
    return NodeHopsResponse(**service.get_hops(node_id=node_id, depth=depth, limit=limit))

from typing import Annotated

from fastapi import APIRouter, Depends

from app.auth.dependencies import require_roles
from app.auth.principal import Principal
from app.auth.rbac import ROLE_ADMIN
from app.schemas.admin import GraphAdminStatusResponse, GraphReloadResponse
from app.services.graph_service import GraphService

router = APIRouter(prefix="/api/admin/graph", tags=["admin-graph"])
service = GraphService()


@router.get("/status", response_model=GraphAdminStatusResponse)
def graph_status(
    _: Annotated[Principal, Depends(require_roles(ROLE_ADMIN))],
) -> GraphAdminStatusResponse:
    return GraphAdminStatusResponse(**service.get_admin_status())


@router.post("/reload", response_model=GraphReloadResponse)
def reload_graph(
    _: Annotated[Principal, Depends(require_roles(ROLE_ADMIN))],
) -> GraphReloadResponse:
    return GraphReloadResponse(**service.reload_graph())

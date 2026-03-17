from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.auth.dependencies import require_roles
from app.auth.principal import Principal
from app.auth.rbac import ROLE_ADMIN
from app.integrations.dify import DifyClientError
from app.schemas.admin import DifyDebugLogListResponse, DifyDebugRequest, DifyDebugResponse
from app.services.dify_debug_service import dify_debug_service
from app.services.runtime_status_service import runtime_status_service

router = APIRouter(prefix="/api/admin/system", tags=["admin-system"])


@router.get("/status")
async def get_system_status(
    _: Annotated[Principal, Depends(require_roles(ROLE_ADMIN))],
) -> dict:
    return await runtime_status_service.get_admin_status()


@router.post("/dify/debug", response_model=DifyDebugResponse)
async def debug_dify(
    payload: DifyDebugRequest,
    _: Annotated[Principal, Depends(require_roles(ROLE_ADMIN))],
) -> DifyDebugResponse:
    try:
        result = await dify_debug_service.run_debug_check(payload)
    except DifyClientError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc
    return DifyDebugResponse(**result)


@router.get("/dify/debug/logs", response_model=DifyDebugLogListResponse)
def list_dify_debug_logs(
    _: Annotated[Principal, Depends(require_roles(ROLE_ADMIN))],
    limit: int = Query(default=20, ge=1, le=100),
) -> DifyDebugLogListResponse:
    return DifyDebugLogListResponse(items=dify_debug_service.list_recent_logs(limit=limit))

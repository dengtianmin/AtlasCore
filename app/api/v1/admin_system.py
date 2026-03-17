from typing import Annotated

from fastapi import APIRouter, Depends

from app.auth.dependencies import require_roles
from app.auth.principal import Principal
from app.auth.rbac import ROLE_ADMIN
from app.services.runtime_status_service import runtime_status_service

router = APIRouter(prefix="/api/admin/system", tags=["admin-system"])


@router.get("/status")
async def get_system_status(
    _: Annotated[Principal, Depends(require_roles(ROLE_ADMIN))],
) -> dict:
    return await runtime_status_service.get_admin_status()

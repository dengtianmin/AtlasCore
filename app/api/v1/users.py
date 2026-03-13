from typing import Annotated

from fastapi import APIRouter, Depends

from app.auth.dependencies import require_roles
from app.auth.principal import Principal
from app.auth.rbac import ROLE_ADMIN, ROLE_USER

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/ping")
def user_ping(
    principal: Annotated[Principal, Depends(require_roles(ROLE_USER, ROLE_ADMIN))],
) -> dict:
    return {"status": "ok", "scope": "user", "user_id": principal.user_id}

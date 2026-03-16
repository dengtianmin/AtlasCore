from fastapi import APIRouter

from app.api.v1.admin import router as admin_router
from app.api.v1.debug import router as debug_router
from app.api.v1.auth import router as auth_router
from app.api.v1.graph import router as graph_router
from app.api.v1.health import router as health_router
from app.api.v1.users import router as users_router

v1_router = APIRouter()
v1_router.include_router(health_router, tags=["health"])
v1_router.include_router(debug_router)
v1_router.include_router(auth_router)
v1_router.include_router(users_router)
v1_router.include_router(admin_router)
v1_router.include_router(graph_router)

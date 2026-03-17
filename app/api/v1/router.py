from fastapi import APIRouter

from app.api.v1.admin import router as admin_router
from app.api.v1.admin_graph import router as admin_graph_router
from app.api.v1.admin_graph_extraction import router as admin_graph_extraction_router
from app.api.v1.admin_review import router as admin_review_router
from app.api.v1.admin_exports import router as admin_exports_router
from app.api.v1.admin_logs import router as admin_logs_router
from app.api.v1.admin_system import router as admin_system_router
from app.api.v1.chat import router as chat_router
from app.api.v1.debug import router as debug_router
from app.api.v1.auth import router as auth_router
from app.api.v1.graph import router as graph_router
from app.api.v1.health import router as health_router
from app.api.v1.root import router as root_router
from app.api.v1.review import router as review_router
from app.api.v1.users import router as users_router

v1_router = APIRouter()
v1_router.include_router(root_router)
v1_router.include_router(health_router, tags=["health"])
v1_router.include_router(debug_router)
v1_router.include_router(auth_router)
v1_router.include_router(users_router)
v1_router.include_router(admin_router)
v1_router.include_router(admin_graph_router)
v1_router.include_router(admin_graph_extraction_router)
v1_router.include_router(admin_review_router)
v1_router.include_router(admin_exports_router)
v1_router.include_router(admin_logs_router)
v1_router.include_router(admin_system_router)
v1_router.include_router(graph_router)
v1_router.include_router(chat_router)
v1_router.include_router(review_router)

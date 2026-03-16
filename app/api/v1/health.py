from fastapi import APIRouter

from app.services.runtime_status_service import runtime_status_service

router = APIRouter()


@router.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/health/ready")
def readiness_check() -> dict:
    return runtime_status_service.get_status()

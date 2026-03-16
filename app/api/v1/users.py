from fastapi import APIRouter

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/ping")
def user_ping() -> dict[str, str]:
    return {"status": "ok", "scope": "anonymous"}

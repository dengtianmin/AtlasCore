from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import settings
from app.core.exceptions import register_exception_handlers


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        debug=settings.is_debug,
    )

    app.include_router(api_router, prefix=settings.API_V1_PREFIX)
    register_exception_handlers(app)

    return app


app = create_app()

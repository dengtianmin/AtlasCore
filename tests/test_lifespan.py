import asyncio

from fastapi import FastAPI

from app.core.lifespan import lifespan


async def _run_lifespan() -> None:
    app = FastAPI()
    async with lifespan(app):
        pass


def test_lifespan_context_runs_without_error():
    asyncio.run(_run_lifespan())

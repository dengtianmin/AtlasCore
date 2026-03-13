from contextlib import asynccontextmanager

from fastapi import FastAPI


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Reserved for future startup/shutdown hooks (DB, Neo4j, integrations).
    yield

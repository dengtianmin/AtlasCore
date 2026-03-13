from functools import lru_cache

from neo4j import Driver, GraphDatabase

from app.core.config import settings


@lru_cache(maxsize=1)
def get_neo4j_driver() -> Driver:
    if not (settings.NEO4J_URI and settings.NEO4J_USERNAME and settings.NEO4J_PASSWORD):
        raise RuntimeError(
            "Neo4j is not configured. Set NEO4J_URI, NEO4J_USERNAME, and NEO4J_PASSWORD."
        )

    return GraphDatabase.driver(
        settings.NEO4J_URI,
        auth=(settings.NEO4J_USERNAME, settings.NEO4J_PASSWORD),
    )

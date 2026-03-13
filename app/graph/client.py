from typing import Any

from neo4j import Driver
from neo4j.exceptions import Neo4jError

from app.core.config import settings
from app.db.neo4j import get_neo4j_driver
from app.graph.exceptions import GraphQueryError, GraphUnavailableError


class GraphClient:
    def __init__(self, driver: Driver | None = None) -> None:
        try:
            self.driver = driver or get_neo4j_driver()
        except RuntimeError as exc:
            raise GraphUnavailableError(str(exc)) from exc

    def run_query(self, cypher: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        query_params = params or {}
        database = settings.NEO4J_DATABASE if settings.NEO4J_DATABASE else None

        try:
            with self.driver.session(database=database) as session:
                result = session.run(cypher, query_params)
                return [record.data() for record in result]
        except Neo4jError as exc:
            raise GraphQueryError("Neo4j query execution failed") from exc

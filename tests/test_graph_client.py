import pytest

import app.graph.client as graph_client_module
from app.graph.client import GraphClient
from app.graph.exceptions import GraphQueryError, GraphUnavailableError
from app.core.config import settings


class FakeRecord:
    def __init__(self, payload):
        self._payload = payload

    def data(self):
        return self._payload


class FakeSession:
    def __init__(self, should_fail=False):
        self.should_fail = should_fail

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def run(self, _cypher, _params):
        if self.should_fail:
            raise Exception("boom")
        return [FakeRecord({"ok": True})]


class FakeDriver:
    def __init__(self, should_fail=False):
        self.should_fail = should_fail
        self.last_database = None

    def session(self, database=None):
        self.last_database = database
        return FakeSession(should_fail=self.should_fail)


def test_graph_client_init_raises_when_unconfigured(monkeypatch):
    def _raise_runtime_error():
        raise RuntimeError("neo4j missing")

    monkeypatch.setattr(graph_client_module, "get_neo4j_driver", _raise_runtime_error)

    with pytest.raises(GraphUnavailableError, match="neo4j missing"):
        GraphClient()


def test_graph_client_run_query_success(monkeypatch):
    monkeypatch.setattr(settings, "NEO4J_DATABASE", "neo4j")
    driver = FakeDriver(should_fail=False)
    client = GraphClient(driver=driver)

    rows = client.run_query("RETURN 1", {"x": 1})

    assert rows == [{"ok": True}]
    assert driver.last_database == "neo4j"


def test_graph_client_run_query_wraps_neo4j_error(monkeypatch):
    monkeypatch.setattr(graph_client_module, "Neo4jError", Exception)
    driver = FakeDriver(should_fail=True)
    client = GraphClient(driver=driver)

    with pytest.raises(GraphQueryError, match="Neo4j query execution failed"):
        client.run_query("RETURN 1")

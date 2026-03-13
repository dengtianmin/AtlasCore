from fastapi import HTTPException

from app.graph.exceptions import GraphUnavailableError
from app.services.graph_service import GraphService


class _Node:
    def __init__(self, element_id: str, labels: list[str], props: dict):
        self.element_id = element_id
        self.labels = set(labels)
        self._props = props

    def __iter__(self):
        return iter(self._props)

    def __getitem__(self, item):
        return self._props[item]

    def keys(self):
        return self._props.keys()

    def __len__(self):
        return len(self._props)


class _Rel:
    def __init__(self, element_id: str, rel_type: str, source: str, target: str, props: dict):
        self.element_id = element_id
        self.type = rel_type
        self.start_node_element_id = source
        self.end_node_element_id = target
        self._props = props

    def __iter__(self):
        return iter(self._props)

    def __getitem__(self, item):
        return self._props[item]

    def keys(self):
        return self._props.keys()

    def __len__(self):
        return len(self._props)


class FakeGraphRepo:
    def fetch_overview(self, *, limit: int):
        n1 = _Node("n1", ["Entity"], {"name": "Alice"})
        n2 = _Node("n2", ["Entity"], {"name": "Bob"})
        r1 = _Rel("r1", "KNOWS", "n1", "n2", {})
        return [{"n": n1, "r": r1}, {"n": n2}]

    def fetch_node(self, *, node_id: str):
        if node_id == "missing":
            return []
        return [{"n": _Node(node_id, ["Entity"], {"name": "X"})}]

    def fetch_neighbors(self, *, node_id: str, limit: int):
        return self.fetch_overview(limit=limit)

    def fetch_hops(self, *, node_id: str, depth: int, limit: int):
        return self.fetch_overview(limit=limit)


class UnavailableRepo(FakeGraphRepo):
    def fetch_overview(self, *, limit: int):
        raise GraphUnavailableError("neo4j down")


def test_get_overview_maps_nodes_and_edges():
    service = GraphService(repo=FakeGraphRepo())

    payload = service.get_overview(limit=50)

    assert payload["total_nodes"] == 2
    assert payload["total_edges"] == 1


def test_get_node_details_not_found():
    service = GraphService(repo=FakeGraphRepo())

    try:
        service.get_node_details(node_id="missing")
        raised = False
    except HTTPException as exc:
        raised = True
        assert exc.status_code == 404

    assert raised is True


def test_get_hops_invalid_depth():
    service = GraphService(repo=FakeGraphRepo())

    try:
        service.get_hops(node_id="n1", depth=3, limit=10)
        raised = False
    except HTTPException as exc:
        raised = True
        assert exc.status_code == 422

    assert raised is True


def test_graph_unavailable_returns_503():
    service = GraphService(repo=UnavailableRepo())

    try:
        service.get_overview(limit=10)
        raised = False
    except HTTPException as exc:
        raised = True
        assert exc.status_code == 503
        assert "Graph backend unavailable" in exc.detail

    assert raised is True

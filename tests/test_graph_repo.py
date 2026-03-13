from app.repositories.graph_repo import GraphRepository


class FakeClient:
    def __init__(self):
        self.calls = []

    def run_query(self, cypher: str, params: dict):
        self.calls.append((cypher, params))
        return [{"ok": True}]


def test_graph_repo_queries_and_params():
    client = FakeClient()
    repo = GraphRepository(client=client)

    repo.fetch_overview(limit=10)
    repo.fetch_node(node_id="n1")
    repo.fetch_neighbors(node_id="n1", limit=20)
    repo.fetch_hops(node_id="n1", depth=1, limit=30)
    repo.fetch_hops(node_id="n1", depth=2, limit=40)

    assert len(client.calls) == 5

    assert "LIMIT $limit" in client.calls[0][0]
    assert client.calls[0][1] == {"limit": 10}

    assert "elementId(n) = $node_id" in client.calls[1][0]
    assert client.calls[1][1] == {"node_id": "n1"}

    assert "OPTIONAL MATCH (n)-[r]-(m)" in client.calls[2][0]
    assert client.calls[2][1] == {"node_id": "n1", "limit": 20}

    assert "[*1..1]" in client.calls[3][0]
    assert client.calls[3][1] == {"node_id": "n1", "limit": 30}

    assert "[*1..2]" in client.calls[4][0]
    assert client.calls[4][1] == {"node_id": "n1", "limit": 40}

from app.graph.mapper import map_records_to_graph


class FakeNode:
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


class FakeRel:
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


def test_map_records_to_graph_deduplicates_nodes_and_edges():
    n1 = FakeNode("n1", ["Entity"], {"name": "Alice"})
    n2 = FakeNode("n2", ["Entity"], {"name": "Bob"})
    r1 = FakeRel("r1", "KNOWS", "n1", "n2", {"weight": 1})

    records = [
        {"n": n1, "r": r1, "m": n2},
        {"n": n1, "r": r1},
    ]

    graph = map_records_to_graph(records)

    assert len(graph["nodes"]) == 2
    assert len(graph["edges"]) == 1

    node_ids = {node["id"] for node in graph["nodes"]}
    edge_ids = {edge["id"] for edge in graph["edges"]}
    assert node_ids == {"n1", "n2"}
    assert edge_ids == {"r1"}

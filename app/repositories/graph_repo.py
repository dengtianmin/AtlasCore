from app.graph.client import GraphClient


class GraphRepository:
    def __init__(self, client: GraphClient | None = None) -> None:
        self.client = client or GraphClient()

    def fetch_overview(self, *, limit: int) -> list[dict]:
        cypher = (
            "MATCH (n) "
            "OPTIONAL MATCH (n)-[r]-() "
            "RETURN n, r "
            "LIMIT $limit"
        )
        return self.client.run_query(cypher, {"limit": limit})

    def fetch_node(self, *, node_id: str) -> list[dict]:
        cypher = "MATCH (n) WHERE elementId(n) = $node_id RETURN n"
        return self.client.run_query(cypher, {"node_id": node_id})

    def fetch_neighbors(self, *, node_id: str, limit: int) -> list[dict]:
        cypher = (
            "MATCH (n) WHERE elementId(n) = $node_id "
            "OPTIONAL MATCH (n)-[r]-(m) "
            "RETURN n, r, m "
            "LIMIT $limit"
        )
        return self.client.run_query(cypher, {"node_id": node_id, "limit": limit})

    def fetch_hops(self, *, node_id: str, depth: int, limit: int) -> list[dict]:
        if depth == 1:
            rel_pattern = "[*1..1]"
        else:
            rel_pattern = "[*1..2]"

        cypher = (
            "MATCH (start) WHERE elementId(start) = $node_id "
            f"MATCH p=(start)-{rel_pattern}-(x) "
            "UNWIND nodes(p) AS n "
            "UNWIND relationships(p) AS r "
            "RETURN DISTINCT n, r "
            "LIMIT $limit"
        )
        return self.client.run_query(cypher, {"node_id": node_id, "limit": limit})

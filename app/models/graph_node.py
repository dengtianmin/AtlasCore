import re

from sqlalchemy import Index, String, Text, event
from sqlalchemy.orm import Mapped, mapped_column

from app.graph.db import GraphBase
from app.models.base import TimestampMixin


class GraphNode(GraphBase, TimestampMixin):
    __tablename__ = "graph_nodes"

    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    normalized_name: Mapped[str] = mapped_column(String(255), nullable=False)
    node_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    source_document: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    tags_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index("ix_graph_nodes_node_type", "node_type"),
        Index("ix_graph_nodes_normalized_name", "normalized_name"),
    )


def normalize_graph_node_name(name: str | None, fallback: str | None = None) -> str:
    raw_value = (name or fallback or "").strip().lower()
    return re.sub(r"\s+", "", raw_value)


@event.listens_for(GraphNode, "before_insert")
@event.listens_for(GraphNode, "before_update")
def _populate_normalized_name(_mapper, _connection, target: GraphNode) -> None:
    target.normalized_name = normalize_graph_node_name(target.name, target.id)

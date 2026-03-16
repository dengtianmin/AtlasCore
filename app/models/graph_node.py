from sqlalchemy import Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.graph.db import GraphBase
from app.models.base import TimestampMixin


class GraphNode(GraphBase, TimestampMixin):
    __tablename__ = "graph_nodes"

    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    node_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    source_document: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    tags_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index("ix_graph_nodes_node_type", "node_type"),
    )

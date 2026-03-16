from sqlalchemy import Float, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.graph.db import GraphBase
from app.models.base import TimestampMixin


class GraphEdge(GraphBase, TimestampMixin):
    __tablename__ = "graph_edges"

    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    source_id: Mapped[str] = mapped_column(String(128), nullable=False)
    target_id: Mapped[str] = mapped_column(String(128), nullable=False)
    relation_type: Mapped[str] = mapped_column(String(100), nullable=False)
    relation_label: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_document: Mapped[str | None] = mapped_column(String(255), nullable=True)
    weight: Mapped[float | None] = mapped_column(Float, nullable=True)
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index("ix_graph_edges_source_id", "source_id"),
        Index("ix_graph_edges_target_id", "target_id"),
        Index("ix_graph_edges_relation_type", "relation_type"),
    )

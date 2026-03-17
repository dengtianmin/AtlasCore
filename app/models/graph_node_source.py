from sqlalchemy import ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.graph.db import GraphBase
from app.models.base import TimestampMixin


class GraphNodeSource(GraphBase, TimestampMixin):
    __tablename__ = "graph_node_sources"

    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    node_id: Mapped[str] = mapped_column(String(128), ForeignKey("graph_nodes.id", ondelete="CASCADE"), nullable=False)
    document_id: Mapped[str] = mapped_column(String(36), nullable=False)
    source_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)

    __table_args__ = (
        UniqueConstraint("node_id", "document_id", name="uq_graph_node_sources_node_document"),
        Index("ix_graph_node_sources_document_id", "document_id"),
    )

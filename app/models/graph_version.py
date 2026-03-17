from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.graph.db import GraphBase
from app.db.types import GUID


class GraphVersion(GraphBase):
    __tablename__ = "graph_versions"

    id: Mapped[UUID] = mapped_column(GUID(), primary_key=True, default=uuid4)
    version: Mapped[str] = mapped_column(String(64), nullable=False)
    version_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    build_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    source_batch: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_document_ids: Mapped[str | None] = mapped_column(Text, nullable=True)
    exported_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    imported_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    operator: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_current: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="0")

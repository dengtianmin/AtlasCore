from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.types import GUID


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[UUID] = mapped_column(GUID(), primary_key=True, default=uuid4)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False, default="manual")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft")
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    synced_to_dify: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    synced_to_graph: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_uri: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_type: Mapped[str | None] = mapped_column(String(120), nullable=True)
    file_size: Mapped[int | None] = mapped_column(nullable=True)
    created_by: Mapped[UUID | None] = mapped_column(
        GUID(), ForeignKey("admin_accounts.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
    last_sync_target: Mapped[str | None] = mapped_column(String(32), nullable=True)
    last_sync_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

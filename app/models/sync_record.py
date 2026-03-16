from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.types import GUID
from app.models.base import TimestampMixin


class SyncRecord(Base, TimestampMixin):
    __tablename__ = "sync_records"

    id: Mapped[UUID] = mapped_column(GUID(), primary_key=True, default=uuid4)
    document_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    target_system: Mapped[str] = mapped_column(String(64), nullable=False, default="dify")
    sync_status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    external_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

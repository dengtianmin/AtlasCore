from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.types import GUID


class FeedbackRecord(Base):
    __tablename__ = "feedback_records"

    id: Mapped[UUID] = mapped_column(GUID(), primary_key=True, default=uuid4)
    qa_log_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("qa_logs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    rating: Mapped[int | None] = mapped_column(nullable=True)
    liked: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str] = mapped_column(String(64), nullable=False, default="anonymous")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

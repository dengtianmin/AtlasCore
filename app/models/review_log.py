from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.types import GUID


class ReviewLog(Base):
    __tablename__ = "review_logs"

    id: Mapped[UUID] = mapped_column(GUID(), primary_key=True, default=uuid4)
    user_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    student_id_snapshot: Mapped[str | None] = mapped_column(String(10), nullable=True)
    name_snapshot: Mapped[str | None] = mapped_column(String(50), nullable=True)
    review_input: Mapped[str] = mapped_column(Text, nullable=False)
    review_result: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_response: Mapped[str | None] = mapped_column(Text, nullable=True)
    normalized_result: Mapped[str | None] = mapped_column(Text, nullable=True)
    parse_status: Mapped[str] = mapped_column(String(32), nullable=False, default="failed")
    score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    risk_level: Mapped[str | None] = mapped_column(String(32), nullable=True)
    engine_source: Mapped[str] = mapped_column(String(64), nullable=False, default="review_dify")
    app_mode: Mapped[str | None] = mapped_column(String(32), nullable=True)
    workflow_run_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    provider_message_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

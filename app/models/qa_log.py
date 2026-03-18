from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.types import GUID


class QuestionAnswerLog(Base):
    __tablename__ = "qa_logs"

    id: Mapped[UUID] = mapped_column(GUID(), primary_key=True, default=uuid4)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    retrieved_context: Mapped[str | None] = mapped_column(Text, nullable=True)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    user_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    student_id_snapshot: Mapped[str | None] = mapped_column(String(10), nullable=True)
    name_snapshot: Mapped[str | None] = mapped_column(String(50), nullable=True)
    session_id: Mapped[str | None] = mapped_column(String(128), index=True, nullable=True)
    source: Mapped[str] = mapped_column(String(64), nullable=False, default="dify")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="succeeded")
    provider_message_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)

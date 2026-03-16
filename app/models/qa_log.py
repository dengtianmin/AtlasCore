from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.types import GUID


class QuestionAnswerLog(Base):
    __tablename__ = "qa_logs"

    id: Mapped[UUID] = mapped_column(GUID(), primary_key=True, default=uuid4)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    retrieved_context: Mapped[str | None] = mapped_column(Text, nullable=True)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    rating: Mapped[int | None] = mapped_column(nullable=True)
    liked: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    session_id: Mapped[str | None] = mapped_column(String(128), index=True, nullable=True)
    source: Mapped[str] = mapped_column(String(64), nullable=False, default="dify")

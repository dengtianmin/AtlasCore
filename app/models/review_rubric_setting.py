from uuid import UUID, uuid4

from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.types import GUID
from app.models.base import TimestampMixin


class ReviewRubricSetting(Base, TimestampMixin):
    __tablename__ = "review_rubric_settings"

    id: Mapped[UUID] = mapped_column(GUID(), primary_key=True, default=uuid4)
    rubric_text: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    updated_by: Mapped[str | None] = mapped_column(String(100), nullable=True)

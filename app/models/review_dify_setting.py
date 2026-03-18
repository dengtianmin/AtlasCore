from sqlalchemy import Boolean, Float, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.base import TimestampMixin


class ReviewDifySetting(Base, TimestampMixin):
    __tablename__ = "review_dify_settings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    app_mode: Mapped[str] = mapped_column(String(32), nullable=False, default="workflow")
    response_mode: Mapped[str] = mapped_column(String(32), nullable=False, default="blocking")
    timeout_seconds: Mapped[float] = mapped_column(Float, nullable=False, default=30.0)
    workflow_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    text_input_variable: Mapped[str | None] = mapped_column(String(128), nullable=True)
    file_input_variable: Mapped[str | None] = mapped_column(String(128), nullable=True)
    enable_trace: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    user_prefix: Mapped[str] = mapped_column(String(64), nullable=False, default="review")
    updated_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

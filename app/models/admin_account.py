from uuid import UUID, uuid4

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.types import GUID
from app.models.base import TimestampMixin


class AdminAccount(Base, TimestampMixin):
    __tablename__ = "admin_accounts"

    id: Mapped[UUID] = mapped_column(GUID(), primary_key=True, default=uuid4)
    username: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

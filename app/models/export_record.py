from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.types import GUID


class ExportRecord(Base):
    __tablename__ = "export_records"

    id: Mapped[UUID] = mapped_column(GUID(), primary_key=True, default=uuid4)
    export_type: Mapped[str] = mapped_column(String(64), nullable=False)
    export_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    record_count: Mapped[int] = mapped_column(Integer, nullable=False)
    operator: Mapped[str] = mapped_column(String(100), nullable=False)
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)

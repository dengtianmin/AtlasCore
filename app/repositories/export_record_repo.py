from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.export_record import ExportRecord


class ExportRecordRepository:
    def create(
        self,
        db: Session,
        *,
        export_type: str,
        export_time: datetime,
        record_count: int,
        operator: str,
        file_path: str,
    ) -> ExportRecord:
        record = ExportRecord(
            export_type=export_type,
            export_time=export_time,
            record_count=record_count,
            operator=operator,
            file_path=file_path,
        )
        db.add(record)
        db.flush()
        db.refresh(record)
        return record

    def list_all(self, db: Session) -> list[ExportRecord]:
        stmt = select(ExportRecord).order_by(ExportRecord.export_time.desc())
        return list(db.execute(stmt).scalars().all())

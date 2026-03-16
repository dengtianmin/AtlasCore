import csv
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import settings
from app.repositories.export_record_repo import ExportRecordRepository
from app.repositories.qa_log_repo import QuestionAnswerLogRepository


class CsvExportService:
    def __init__(self) -> None:
        self.qa_log_repo = QuestionAnswerLogRepository()
        self.export_record_repo = ExportRecordRepository()

    def export_qa_logs(self, db: Session, *, operator: str) -> dict:
        export_dir = Path(settings.CSV_EXPORT_DIR).expanduser()
        export_dir.mkdir(parents=True, exist_ok=True)

        records = self.qa_log_repo.list_all(db, limit=100000, offset=0)
        timestamp = datetime.now(UTC)
        file_path = export_dir / f"qa_logs_{timestamp.strftime('%Y%m%d_%H%M%S')}.csv"

        with file_path.open("w", encoding="utf-8", newline="") as csv_file:
            writer = csv.DictWriter(
                csv_file,
                fieldnames=[
                    "id",
                    "question",
                    "retrieved_context",
                    "answer",
                    "rating",
                    "liked",
                    "created_at",
                    "session_id",
                    "source",
                ],
            )
            writer.writeheader()
            for record in records:
                writer.writerow(
                    {
                        "id": str(record.id),
                        "question": record.question,
                        "retrieved_context": record.retrieved_context or "",
                        "answer": record.answer,
                        "rating": record.rating if record.rating is not None else "",
                        "liked": record.liked if record.liked is not None else "",
                        "created_at": record.created_at.isoformat(),
                        "session_id": record.session_id or "",
                        "source": record.source,
                    }
                )

        export_record = self.export_record_repo.create(
            db,
            export_type="qa_logs",
            export_time=timestamp,
            record_count=len(records),
            operator=operator,
            file_path=str(file_path),
        )
        db.commit()
        return {
            "id": export_record.id,
            "export_type": export_record.export_type,
            "export_time": export_record.export_time,
            "record_count": export_record.record_count,
            "operator": export_record.operator,
            "file_path": export_record.file_path,
        }

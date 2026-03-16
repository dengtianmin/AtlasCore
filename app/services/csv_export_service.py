import csv
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from urllib.parse import quote
import logging

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import get_logger, log_event
from app.repositories.export_record_repo import ExportRecordRepository
from app.repositories.qa_log_repo import QuestionAnswerLogRepository
from app.services.runtime_status_service import runtime_status_service

logger = get_logger(__name__)


class CsvExportService:
    def __init__(self) -> None:
        self.qa_log_repo = QuestionAnswerLogRepository()
        self.export_record_repo = ExportRecordRepository()

    def export_qa_logs(self, db: Session, *, operator: str) -> dict:
        started = perf_counter()
        export_dir = Path(settings.CSV_EXPORT_DIR).expanduser()
        export_dir.mkdir(parents=True, exist_ok=True)
        log_event(
            logger,
            logging.INFO,
            "csv_export",
            "started",
            export_type="qa_logs",
            operator=operator,
            target_dir=str(export_dir),
        )

        try:
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
                            "created_at": record.created_at.isoformat(),
                            "session_id": record.session_id or "",
                            "source": record.source,
                        }
                    )
            log_event(
                logger,
                logging.INFO,
                "csv_export_write",
                "success",
                export_type="qa_logs",
                target_path=str(file_path),
                record_count=len(records),
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
            payload = self._to_payload(export_record, success=True)
            runtime_status_service.record_csv_export(
                {
                    "status": "success",
                    "export_type": "qa_logs",
                    "filename": payload["filename"],
                    "record_count": len(records),
                    "operator": operator,
                }
            )
            log_event(
                logger,
                logging.INFO,
                "csv_export",
                "success",
                export_type="qa_logs",
                target_path=str(file_path),
                record_count=len(records),
                duration_ms=round((perf_counter() - started) * 1000, 2),
            )
            return payload
        except Exception as exc:
            runtime_status_service.record_error(error_type="csv_export_error", detail=str(exc))
            runtime_status_service.record_csv_export(
                {
                    "status": "failed",
                    "export_type": "qa_logs",
                    "operator": operator,
                    "detail": str(exc),
                }
            )
            log_event(
                logger,
                logging.ERROR,
                "csv_export",
                "failed",
                error_type="csv_export_error",
                detail=str(exc),
                export_type="qa_logs",
                operator=operator,
            )
            raise

    def list_exports(self, db: Session) -> dict:
        records = self.export_record_repo.list_all(db)
        return {"items": [self._to_payload(record) for record in records]}

    def get_latest_export(self, db: Session) -> dict | None:
        records = self.export_record_repo.list_all(db)
        if not records:
            return None
        return self._to_payload(records[0])

    def resolve_download_path(self, filename: str) -> Path:
        if not filename or filename != Path(filename).name or not filename.endswith(".csv"):
            log_event(
                logger,
                logging.WARNING,
                "csv_export_download",
                "failed",
                error_type="csv_export_error",
                detail="Invalid export filename",
                filename=filename,
            )
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid export filename")

        export_dir = Path(settings.CSV_EXPORT_DIR).expanduser().resolve()
        file_path = (export_dir / filename).resolve()
        if file_path.parent != export_dir:
            log_event(
                logger,
                logging.WARNING,
                "csv_export_download",
                "failed",
                error_type="csv_export_error",
                detail="Invalid export filename",
                filename=filename,
            )
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid export filename")
        if not file_path.exists() or not file_path.is_file():
            log_event(
                logger,
                logging.WARNING,
                "csv_export_download",
                "failed",
                error_type="csv_export_error",
                detail="Export file not found",
                filename=filename,
            )
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Export file not found")
        log_event(
            logger,
            logging.INFO,
            "csv_export_download",
            "success",
            filename=filename,
            path=str(file_path),
        )
        return file_path

    def _to_payload(self, export_record, *, success: bool | None = None) -> dict:
        filename = Path(export_record.file_path).name
        payload = {
            "export_id": export_record.id,
            "export_type": export_record.export_type,
            "export_time": export_record.export_time,
            "record_count": export_record.record_count,
            "operator": export_record.operator,
            "filename": filename,
            "download_url": f"/api/admin/exports/download/{quote(filename)}",
        }
        if success is not None:
            payload["success"] = success
        return payload

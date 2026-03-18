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
from app.repositories.feedback_repo import FeedbackRepository
from app.repositories.qa_log_repo import QuestionAnswerLogRepository
from app.services.runtime_status_service import runtime_status_service

logger = get_logger(__name__)


class CsvExportService:
    def __init__(self) -> None:
        self.qa_log_repo = QuestionAnswerLogRepository()
        self.feedback_repo = FeedbackRepository()
        self.export_record_repo = ExportRecordRepository()

    def export_qa_logs(self, db: Session, *, operator: str) -> dict:
        started = perf_counter()
        export_dir = Path(settings.CSV_EXPORT_DIR).expanduser()
        export_dir.mkdir(parents=True, exist_ok=True)
        log_event(
            logger,
            logging.INFO,
            "csv_export_started",
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
                        "student_id",
                        "name",
                        "session_id",
                        "source",
                        "status",
                        "provider_message_id",
                        "error_code",
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
                            "student_id": record.student_id_snapshot or "",
                            "name": record.name_snapshot or "",
                            "session_id": record.session_id or "",
                            "source": record.source,
                            "status": record.status,
                            "provider_message_id": record.provider_message_id or "",
                            "error_code": record.error_code or "",
                        }
                    )
            log_event(
                logger,
                logging.INFO,
                "csv_export_succeeded",
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
                "csv_export_succeeded",
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
                "csv_export_failed",
                "failed",
                error_type="csv_export_error",
                detail=str(exc),
                export_type="qa_logs",
                operator=operator,
            )
            raise

    def export_feedback(self, db: Session, *, operator: str) -> dict:
        started = perf_counter()
        export_dir = Path(settings.CSV_EXPORT_DIR).expanduser()
        export_dir.mkdir(parents=True, exist_ok=True)
        log_event(
            logger,
            logging.INFO,
            "csv_export_started",
            "started",
            export_type="feedback",
            operator=operator,
            target_dir=str(export_dir),
        )

        try:
            records = self.feedback_repo.list_all(db, limit=100000, offset=0)
            timestamp = datetime.now(UTC)
            file_path = export_dir / f"feedback_{timestamp.strftime('%Y%m%d_%H%M%S')}.csv"
            with file_path.open("w", encoding="utf-8", newline="") as csv_file:
                writer = csv.DictWriter(
                    csv_file,
                    fieldnames=[
                        "id",
                        "qa_log_id",
                        "rating",
                        "liked",
                        "comment",
                        "student_id",
                        "name",
                        "source",
                        "created_at",
                    ],
                )
                writer.writeheader()
                for record in records:
                    qa_log = self.qa_log_repo.get_by_id(db, record.qa_log_id)
                    writer.writerow(
                        {
                            "id": str(record.id),
                            "qa_log_id": str(record.qa_log_id),
                            "rating": record.rating if record.rating is not None else "",
                            "liked": record.liked if record.liked is not None else "",
                            "comment": record.comment or "",
                            "student_id": qa_log.student_id_snapshot if qa_log and qa_log.student_id_snapshot else "",
                            "name": qa_log.name_snapshot if qa_log and qa_log.name_snapshot else "",
                            "source": record.source,
                            "created_at": record.created_at.isoformat(),
                        }
                    )

            export_record = self.export_record_repo.create(
                db,
                export_type="feedback",
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
                    "export_type": "feedback",
                    "filename": payload["filename"],
                    "record_count": len(records),
                    "operator": operator,
                }
            )
            log_event(
                logger,
                logging.INFO,
                "csv_export_succeeded",
                "success",
                export_type="feedback",
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
                    "export_type": "feedback",
                    "operator": operator,
                    "detail": str(exc),
                }
            )
            log_event(
                logger,
                logging.ERROR,
                "csv_export_failed",
                "failed",
                error_type="csv_export_error",
                detail=str(exc),
                export_type="feedback",
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

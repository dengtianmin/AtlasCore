from uuid import UUID

from sqlalchemy.orm import Session

from app.models.sync_record import SyncRecord


class SyncRecordRepository:
    def create(
        self,
        db: Session,
        *,
        document_id: UUID,
        target_system: str,
        sync_status: str,
    ) -> SyncRecord:
        record = SyncRecord(
            document_id=document_id,
            target_system=target_system,
            sync_status=sync_status,
        )
        db.add(record)
        db.flush()
        db.refresh(record)
        return record

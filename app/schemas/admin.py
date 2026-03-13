from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.admin.document_status import DocumentStatus


class DocumentUploadResponse(BaseModel):
    id: UUID
    title: str
    status: DocumentStatus
    source_type: str
    source_uri: str | None
    file_name: str | None
    content_type: str | None
    file_size: int | None
    created_by: UUID | None
    created_at: datetime
    updated_at: datetime


class DocumentListResponse(BaseModel):
    items: list[DocumentUploadResponse]


class DocumentStatusResponse(BaseModel):
    id: UUID
    status: DocumentStatus
    updated_at: datetime


class SyncTriggerResponse(BaseModel):
    document_id: UUID
    status: DocumentStatus
    sync_record_id: UUID
    target_system: str
    message: str

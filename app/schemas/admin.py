from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.admin.document_status import DocumentStatus


class DocumentUploadResponse(BaseModel):
    id: UUID
    filename: str
    status: DocumentStatus
    source_type: str
    uploaded_at: datetime
    synced_to_dify: bool
    synced_to_graph: bool
    note: str | None
    source_uri: str | None
    content_type: str | None
    file_size: int | None
    created_by: UUID | None


class DocumentListResponse(BaseModel):
    items: list[DocumentUploadResponse]


class DocumentStatusResponse(BaseModel):
    id: UUID
    status: DocumentStatus
    uploaded_at: datetime


class SyncTriggerResponse(BaseModel):
    document_id: UUID
    status: DocumentStatus
    target_system: str
    message: str

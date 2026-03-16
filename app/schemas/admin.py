from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

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


class ExportTriggerRequest(BaseModel):
    operator: str = Field(default="system", min_length=1, max_length=100)


class ExportRecordResponse(BaseModel):
    export_id: UUID
    export_type: str
    export_time: datetime
    record_count: int
    operator: str
    filename: str
    download_url: str


class ExportListResponse(BaseModel):
    items: list[ExportRecordResponse]


class ExportTriggerResponse(ExportRecordResponse):
    success: bool

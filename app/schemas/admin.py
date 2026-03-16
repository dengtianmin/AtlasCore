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
    created_at: datetime
    last_sync_target: str | None = None
    last_sync_status: str | None = None
    last_sync_at: datetime | None = None


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


class GraphAdminStatusResponse(BaseModel):
    enabled: bool
    loaded: bool
    node_count: int
    edge_count: int
    current_version: str | None
    instance_id: str
    graph_db_version: str | None
    sqlite_path: str
    last_loaded_at: datetime | None
    import_dir: str
    export_dir: str
    import_dir_exists: bool
    export_dir_exists: bool
    instance_local_path: str
    instance_local_path_exists: bool
    multi_instance_mode: str


class GraphReloadResponse(BaseModel):
    loaded: bool
    node_count: int
    edge_count: int
    current_version: str | None
    sqlite_path: str
    last_loaded_at: datetime | None


class GraphFileOperationResponse(BaseModel):
    record_id: UUID
    filename: str
    file_path: str
    download_url: str | None = None
    version: str | None
    loaded: bool
    node_count: int
    edge_count: int
    current_version: str | None
    sqlite_path: str
    last_loaded_at: datetime | None

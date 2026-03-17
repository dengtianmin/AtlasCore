from datetime import datetime
from typing import Any
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
    local_path: str | None = None
    source_uri: str | None
    mime_type: str | None = None
    content_type: str | None
    file_size: int | None
    file_extension: str | None = None
    dify_upload_file_id: str | None = None
    dify_uploaded_at: datetime | None = None
    dify_sync_status: str | None = None
    dify_error_code: str | None = None
    dify_error_message: str | None = None
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


class DifyDebugRequest(BaseModel):
    base_url: str = Field(min_length=1, max_length=500)
    api_key: str = Field(min_length=1, max_length=2000)
    timeout_seconds: float = Field(default=15.0, gt=0, le=120)
    workflow_id: str | None = Field(default=None, max_length=255)
    response_mode: str = Field(default="blocking", max_length=32)
    text_input_variable: str | None = Field(default=None, max_length=128)
    file_input_variable: str | None = Field(default=None, max_length=128)
    enable_trace: bool = False
    user_prefix: str = Field(default="debug", min_length=1, max_length=64)
    sample_text: str | None = Field(default=None, max_length=4000)


class DifyDebugResponse(BaseModel):
    reachable: bool
    validation_ok: bool
    config_summary: dict[str, Any]
    parameters: dict[str, Any] | None = None
    info: dict[str, Any] | None = None
    workflow_result: dict[str, Any] | None = None
    warnings: list[str] = Field(default_factory=list)
    logs_saved_to: str


class DifyDebugLogRecord(BaseModel):
    recorded_at: datetime
    event: str
    status: str
    payload: dict[str, Any] = Field(default_factory=dict)


class DifyDebugLogListResponse(BaseModel):
    items: list[DifyDebugLogRecord]

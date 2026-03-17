from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class DifySettings(BaseModel):
    base_url: str | None = None
    api_key: str | None = None
    timeout_seconds: float = Field(default=15.0, gt=0)
    workflow_id: str | None = None
    response_mode: Literal["blocking", "streaming"] = "blocking"
    text_input_variable: str | None = None
    file_input_variable: str | None = None
    enable_trace: bool = False
    user_prefix: str = "guest"

    @property
    def enabled(self) -> bool:
        return bool(self.base_url and self.api_key)


class DifyWorkflowResult(BaseModel):
    workflow_run_id: str | None = None
    task_id: str | None = None
    status: str | None = None
    outputs: dict[str, Any] = Field(default_factory=dict)
    error: str | dict[str, Any] | None = None
    elapsed_time: float | None = None
    total_tokens: int | None = None
    total_steps: int | None = None
    raw: dict[str, Any] = Field(default_factory=dict)


class DifyUploadedFile(BaseModel):
    file_id: str
    name: str | None = None
    size: int | None = None
    extension: str | None = None
    mime_type: str | None = None
    created_at: int | None = None
    raw: dict[str, Any] = Field(default_factory=dict)


class DifyValidationResult(BaseModel):
    ok: bool
    reachable: bool
    text_input_variable_exists: bool
    file_input_variable_exists: bool
    file_upload_enabled: bool
    warnings: list[str] = Field(default_factory=list)
    raw_parameters: dict[str, Any] = Field(default_factory=dict)


class DifyDocumentIndexRequest(BaseModel):
    document_id: str
    title: str
    source_uri: str | None = None


class DifyJobResponse(BaseModel):
    job_id: str
    status: str
    message: str


class DifyChatRequest(BaseModel):
    query: str
    session_id: str
    user: str = "anonymous"
    trace_id: str | None = None


class DifyChatSource(BaseModel):
    title: str
    snippet: str | None = None
    source: str | None = None


class DifyChatResponse(BaseModel):
    answer: str
    source: str = "dify"
    sources: list[DifyChatSource] = Field(default_factory=list)
    retrieved_context: str | None = None
    session_id: str | None = None
    provider_message_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

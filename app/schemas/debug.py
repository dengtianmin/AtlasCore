from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class QuestionAnswerLogCreateRequest(BaseModel):
    question: str = Field(min_length=1)
    retrieved_context: str | None = None
    answer: str = Field(min_length=1)
    rating: int | None = Field(default=None, ge=1, le=5)
    liked: bool | None = None
    session_id: str | None = Field(default=None, max_length=128)
    source: str = Field(default="dify", min_length=1, max_length=64)


class QuestionAnswerLogResponse(BaseModel):
    id: UUID
    question: str
    retrieved_context: str | None
    answer: str
    rating: int | None
    liked: bool | None
    created_at: datetime
    session_id: str | None
    source: str


class QuestionAnswerLogListResponse(BaseModel):
    items: list[QuestionAnswerLogResponse]


class ExportRequest(BaseModel):
    operator: str = Field(default="system", min_length=1, max_length=100)


class ExportResponse(BaseModel):
    id: UUID
    export_type: str
    export_time: datetime
    record_count: int
    operator: str
    file_path: str

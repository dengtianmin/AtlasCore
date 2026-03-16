from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class QuestionAnswerLogCreateRequest(BaseModel):
    question: str = Field(min_length=1)
    retrieved_context: str | None = None
    answer: str = Field(min_length=1)
    session_id: str | None = Field(default=None, max_length=128)
    source: str = Field(default="dify", min_length=1, max_length=64)


class QuestionAnswerLogResponse(BaseModel):
    id: UUID
    question: str
    retrieved_context: str | None
    answer: str
    created_at: datetime
    session_id: str | None
    source: str


class QuestionAnswerLogListResponse(BaseModel):
    items: list[QuestionAnswerLogResponse]


class FeedbackCreateRequest(BaseModel):
    rating: int | None = Field(default=None, ge=1, le=5)
    liked: bool | None = None
    comment: str | None = Field(default=None, max_length=1000)
    source: str = Field(default="anonymous", min_length=1, max_length=64)


class FeedbackResponse(BaseModel):
    id: UUID
    qa_log_id: UUID
    rating: int | None
    liked: bool | None
    comment: str | None
    source: str
    created_at: datetime


class FeedbackListResponse(BaseModel):
    items: list[FeedbackResponse]


class ExportRequest(BaseModel):
    operator: str = Field(default="system", min_length=1, max_length=100)


class ExportResponse(BaseModel):
    id: UUID
    export_type: str
    export_time: datetime
    record_count: int
    operator: str
    file_path: str

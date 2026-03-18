from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class LogFeedbackSummary(BaseModel):
    id: UUID
    rating: int | None
    liked: bool | None
    comment: str | None
    source: str
    created_at: datetime


class AdminLogRecordResponse(BaseModel):
    id: UUID
    question: str
    retrieved_context: str | None
    answer: str
    created_at: datetime
    user_id: UUID | None = None
    student_id_snapshot: str | None = None
    name_snapshot: str | None = None
    session_id: str | None
    source: str
    status: str
    provider_message_id: str | None
    error_code: str | None
    feedback_count: int = 0
    feedback: LogFeedbackSummary | None = None


class AdminLogListResponse(BaseModel):
    items: list[AdminLogRecordResponse]


class FeedbackRecordResponse(BaseModel):
    id: UUID
    qa_log_id: UUID
    student_id_snapshot: str | None = None
    name_snapshot: str | None = None
    rating: int | None
    liked: bool | None
    comment: str | None
    source: str
    created_at: datetime


class FeedbackRecordListResponse(BaseModel):
    items: list[FeedbackRecordResponse]

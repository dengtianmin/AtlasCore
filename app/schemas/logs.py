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
    session_id: str | None
    source: str
    feedback: LogFeedbackSummary | None = None


class AdminLogListResponse(BaseModel):
    items: list[AdminLogRecordResponse]

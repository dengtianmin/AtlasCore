from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class ChatMessageRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)
    session_id: str | None = Field(default=None, max_length=128)


class ChatMessageResponse(BaseModel):
    message_id: UUID
    session_id: str
    answer: str
    source: str
    sources: list[str]
    retrieved_context: str | None = None
    status: str
    provider_message_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class ChatFeedbackRequest(BaseModel):
    rating: int | None = Field(default=None, ge=1, le=5)
    liked: bool | None = None
    comment: str | None = Field(default=None, max_length=1000)
    source: str = Field(default="anonymous", min_length=1, max_length=64)


class ChatFeedbackResponse(BaseModel):
    id: UUID
    qa_log_id: UUID
    rating: int | None
    liked: bool | None
    comment: str | None
    source: str
    created_at: datetime

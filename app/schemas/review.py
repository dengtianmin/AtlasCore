from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class ReviewRubricResponse(BaseModel):
    rubric_text: str
    updated_at: datetime | None = None
    updated_by: str | None = None
    is_active: bool


class ReviewRubricUpdateRequest(BaseModel):
    rubric_text: str = Field(min_length=1, max_length=20000)


class ReviewEvaluationRequest(BaseModel):
    answer_text: str = Field(min_length=1, max_length=12000)


class ReviewItem(BaseModel):
    item_name: str = ""
    conclusion: str = ""
    importance: str = ""
    scheme_excerpt: str = ""
    standard_basis: str = ""
    reason: str = ""
    suggestion: str = ""


class ReviewKeyIssue(BaseModel):
    title: str = ""
    risk_level: str = ""
    problem: str = ""
    basis: str = ""
    suggestion: str = ""


class ReviewDeductionLogicItem(BaseModel):
    reason: str = ""
    deducted_score: float | int = 0


class ReviewResultData(BaseModel):
    type: str = "review_result"
    score: int | None = None
    grade: str | None = None
    risk_level: str | None = None
    summary: str = ""
    review_items: list[ReviewItem] = Field(default_factory=list)
    key_issues: list[ReviewKeyIssue] = Field(default_factory=list)
    deduction_logic: list[ReviewDeductionLogicItem] = Field(default_factory=list)
    raw_text: str | None = None
    parse_status: str = "failed"


class ReviewEvaluationResponse(ReviewResultData):
    review_log_id: UUID | None = None
    raw_response: dict[str, Any] | list[Any] | str | None = None
    rubric_updated_at: datetime | None = None
    source: str = "review_dify"
    provider_message_id: str | None = None
    workflow_run_id: str | None = None
    created_at: datetime | None = None


class ReviewDifyConfigSummaryResponse(BaseModel):
    enabled: bool
    base_url: str | None = None
    has_api_key: bool = False
    app_mode: str
    response_mode: str
    timeout_seconds: float
    workflow_id_configured: bool
    text_input_variable: str | None = None
    file_input_variable: str | None = None
    enable_trace: bool
    user_prefix: str


class ReviewDifyConfigUpdateRequest(BaseModel):
    base_url: str | None = Field(default=None, max_length=1000)
    api_key: str | None = Field(default=None, max_length=2000)
    app_mode: str = Field(pattern="^(workflow|chat)$")
    response_mode: str = Field(pattern="^(blocking|streaming)$")
    timeout_seconds: float = Field(gt=0, le=300)
    workflow_id: str | None = Field(default=None, max_length=255)
    text_input_variable: str | None = Field(default=None, max_length=128)
    file_input_variable: str | None = Field(default=None, max_length=128)
    enable_trace: bool = False
    user_prefix: str = Field(default="review", min_length=1, max_length=64)


class ReviewLogRecordResponse(BaseModel):
    id: UUID
    user_id: UUID | None = None
    student_id_snapshot: str | None = None
    name_snapshot: str | None = None
    review_input: str
    review_result: str | None = None
    raw_response: str | None = None
    normalized_result: str | None = None
    parse_status: str
    score: int | None = None
    risk_level: str | None = None
    engine_source: str
    app_mode: str | None = None
    workflow_run_id: str | None = None
    provider_message_id: str | None = None
    created_at: datetime


class ReviewLogListResponse(BaseModel):
    items: list[ReviewLogRecordResponse]

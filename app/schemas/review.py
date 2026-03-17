from datetime import datetime

from pydantic import BaseModel, Field


class ReviewRubricResponse(BaseModel):
    rubric_text: str
    updated_at: datetime | None = None
    updated_by: str | None = None
    is_active: bool


class ReviewRubricUpdateRequest(BaseModel):
    rubric_text: str = Field(min_length=1, max_length=20000)


class ReviewEvaluationRequest(BaseModel):
    answer_text: str = Field(min_length=1, max_length=4000)


class ReviewEvaluationResponse(BaseModel):
    score: int = Field(ge=0, le=100)
    reason: str
    rubric_updated_at: datetime | None = None

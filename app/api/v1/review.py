from collections.abc import Generator
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_active_user_principal
from app.auth.principal import Principal
from app.db.session import get_db_session
from app.schemas.review import ReviewEvaluationRequest, ReviewEvaluationResponse
from app.services.review_service import review_service

router = APIRouter(prefix="/review", tags=["review"])


def get_session() -> Generator[Session, None, None]:
    yield from get_db_session()


@router.post("/evaluate", response_model=ReviewEvaluationResponse)
async def evaluate_review(
    payload: ReviewEvaluationRequest,
    _: Annotated[Principal, Depends(get_current_active_user_principal)],
    db: Annotated[Session, Depends(get_session)],
) -> ReviewEvaluationResponse:
    return ReviewEvaluationResponse(**await review_service.evaluate_answer(db, answer_text=payload.answer_text))

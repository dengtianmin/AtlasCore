from typing import Annotated
from uuid import UUID

from collections.abc import Generator

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.schemas.debug import (
    ExportRequest,
    ExportResponse,
    QuestionAnswerLogCreateRequest,
    QuestionAnswerLogListResponse,
    QuestionAnswerLogResponse,
)
from app.services.csv_export_service import CsvExportService
from app.services.qa_log_service import QuestionAnswerLogService

router = APIRouter(prefix="/debug", tags=["debug"])
qa_log_service = QuestionAnswerLogService()
csv_export_service = CsvExportService()


def get_session() -> Generator[Session, None, None]:
    yield from get_db_session()


@router.post("/qa-logs", response_model=QuestionAnswerLogResponse, status_code=status.HTTP_201_CREATED)
def create_qa_log(
    payload: QuestionAnswerLogCreateRequest,
    db: Annotated[Session, Depends(get_session)],
) -> QuestionAnswerLogResponse:
    return QuestionAnswerLogResponse(
        **qa_log_service.create_log(
            db,
            question=payload.question,
            retrieved_context=payload.retrieved_context,
            answer=payload.answer,
            rating=payload.rating,
            liked=payload.liked,
            session_id=payload.session_id,
            source=payload.source,
        )
    )


@router.get("/qa-logs", response_model=QuestionAnswerLogListResponse)
def list_qa_logs(
    db: Annotated[Session, Depends(get_session)],
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> QuestionAnswerLogListResponse:
    return QuestionAnswerLogListResponse(**qa_log_service.list_logs(db, limit=limit, offset=offset))


@router.get("/qa-logs/{record_id}", response_model=QuestionAnswerLogResponse)
def get_qa_log(
    record_id: UUID,
    db: Annotated[Session, Depends(get_session)],
) -> QuestionAnswerLogResponse:
    payload = qa_log_service.get_log(db, record_id=record_id)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="QA log not found")
    return QuestionAnswerLogResponse(**payload)


@router.post("/exports/qa-logs", response_model=ExportResponse)
def export_qa_logs(
    payload: ExportRequest,
    db: Annotated[Session, Depends(get_session)],
) -> ExportResponse:
    return ExportResponse(**csv_export_service.export_qa_logs(db, operator=payload.operator))

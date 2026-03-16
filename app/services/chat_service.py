from __future__ import annotations

import logging
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.logging import get_logger, log_event
from app.integrations.dify import (
    DifyChatRequest,
    DifyConfigurationError,
    DifyRequestError,
    DifyTimeoutError,
    get_dify_client,
)
from app.services.feedback_service import FeedbackService
from app.services.qa_log_service import QuestionAnswerLogService

logger = get_logger(__name__)


class ChatService:
    def __init__(self) -> None:
        self.qa_log_service = QuestionAnswerLogService()
        self.feedback_service = FeedbackService()
        self.dify_client = get_dify_client()

    def ask(
        self,
        db: Session,
        *,
        question: str,
        session_id: str | None,
    ) -> dict:
        normalized_question = question.strip()
        resolved_session_id = session_id or f"session-{uuid4().hex[:12]}"
        request_id = f"chat-{uuid4().hex[:12]}"

        log_event(
            logger,
            logging.INFO,
            "chat_request_received",
            "started",
            request_id=request_id,
            session_id=resolved_session_id,
        )
        log_event(
            logger,
            logging.INFO,
            "dify_request_started",
            "started",
            request_id=request_id,
            session_id=resolved_session_id,
        )

        try:
            dify_response = self.dify_client.chat(
                DifyChatRequest(
                    query=normalized_question,
                    session_id=resolved_session_id,
                )
            )
        except DifyConfigurationError as exc:
            self._write_failed_log(
                db,
                question=normalized_question,
                session_id=resolved_session_id,
                error_code="dify_not_configured",
                answer="Dify integration is not configured",
            )
            log_event(
                logger,
                logging.WARNING,
                "dify_request_failed",
                "failed",
                request_id=request_id,
                session_id=resolved_session_id,
                error_type="dify_not_configured",
                detail=str(exc),
            )
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Chat integration is not configured",
            ) from exc
        except DifyTimeoutError as exc:
            self._write_failed_log(
                db,
                question=normalized_question,
                session_id=resolved_session_id,
                error_code="dify_timeout",
                answer="Dify request timed out",
            )
            log_event(
                logger,
                logging.ERROR,
                "dify_request_failed",
                "failed",
                request_id=request_id,
                session_id=resolved_session_id,
                error_type="dify_timeout",
                detail=str(exc),
            )
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="Chat provider timed out",
            ) from exc
        except DifyRequestError as exc:
            self._write_failed_log(
                db,
                question=normalized_question,
                session_id=resolved_session_id,
                error_code="dify_request_failed",
                answer="Dify request failed",
            )
            log_event(
                logger,
                logging.ERROR,
                "dify_request_failed",
                "failed",
                request_id=request_id,
                session_id=resolved_session_id,
                error_type="dify_request_failed",
                detail=str(exc),
            )
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Chat provider request failed",
            ) from exc

        payload = self.qa_log_service.create_log(
            db,
            question=normalized_question,
            retrieved_context=dify_response.retrieved_context,
            answer=dify_response.answer,
            session_id=dify_response.session_id or resolved_session_id,
            source=dify_response.source,
            status="succeeded",
            provider_message_id=dify_response.provider_message_id,
            error_code=None,
        )
        log_event(
            logger,
            logging.INFO,
            "dify_request_succeeded",
            "success",
            request_id=request_id,
            session_id=payload["session_id"],
            source=dify_response.source,
            provider_message_id=dify_response.provider_message_id,
        )
        log_event(
            logger,
            logging.INFO,
            "qa_log_written",
            "success",
            request_id=request_id,
            session_id=payload["session_id"],
            qa_log_id=str(payload["id"]),
            source=payload["source"],
            qa_status=payload["status"],
        )
        return {
            "message_id": payload["id"],
            "session_id": payload["session_id"],
            "answer": dify_response.answer,
            "source": dify_response.source,
            "sources": [item.title for item in dify_response.sources],
            "retrieved_context": dify_response.retrieved_context,
            "status": payload["status"],
            "provider_message_id": dify_response.provider_message_id,
            "metadata": dify_response.metadata,
            "created_at": payload["created_at"],
        }

    def create_feedback(
        self,
        db: Session,
        *,
        message_id,
        rating: int | None,
        liked: bool | None,
        comment: str | None,
        source: str,
    ) -> dict:
        return self.feedback_service.create_feedback(
            db,
            qa_log_id=message_id,
            rating=rating,
            liked=liked,
            comment=comment,
            source=source,
        )

    def _write_failed_log(
        self,
        db: Session,
        *,
        question: str,
        session_id: str,
        error_code: str,
        answer: str,
    ) -> None:
        payload = self.qa_log_service.create_log(
            db,
            question=question,
            retrieved_context=None,
            answer=answer,
            session_id=session_id,
            source="dify",
            status="failed",
            provider_message_id=None,
            error_code=error_code,
        )
        log_event(
            logger,
            logging.INFO,
            "qa_log_written",
            "success",
            session_id=session_id,
            qa_log_id=str(payload["id"]),
            source="dify",
            qa_status="failed",
            error_code=error_code,
        )

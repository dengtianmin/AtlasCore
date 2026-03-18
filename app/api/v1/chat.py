from collections.abc import Generator
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import json

from app.auth.dependencies import get_current_active_user_principal
from app.auth.principal import Principal
from app.db.session import get_db_session
from app.schemas.chat import (
    ChatFeedbackRequest,
    ChatFeedbackResponse,
    ChatMessageRequest,
    ChatMessageResponse,
)
from app.services.chat_service import ChatService

router = APIRouter(prefix="/chat", tags=["chat"])
service = ChatService()


def get_session() -> Generator[Session, None, None]:
    yield from get_db_session()


@router.post("/messages", response_model=ChatMessageResponse)
async def send_message(
    payload: ChatMessageRequest,
    principal: Annotated[Principal, Depends(get_current_active_user_principal)],
    db: Annotated[Session, Depends(get_session)],
) -> ChatMessageResponse:
    return ChatMessageResponse(
        **await service.ask(db, question=payload.question, session_id=payload.session_id, principal=principal)
    )


@router.post("/messages/stream")
async def stream_message(
    payload: ChatMessageRequest,
    principal: Annotated[Principal, Depends(get_current_active_user_principal)],
    db: Annotated[Session, Depends(get_session)],
) -> StreamingResponse:
    async def event_generator():
        async for event in service.stream_ask(db, question=payload.question, session_id=payload.session_id, principal=principal):
            yield f"event: {event['event']}\ndata: {json.dumps(event['data'], ensure_ascii=False)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/messages/{message_id}/feedback", response_model=ChatFeedbackResponse)
def submit_feedback(
    message_id: UUID,
    payload: ChatFeedbackRequest,
    _: Annotated[Principal, Depends(get_current_active_user_principal)],
    db: Annotated[Session, Depends(get_session)],
) -> ChatFeedbackResponse:
    return ChatFeedbackResponse(
        **service.create_feedback(
            db,
            message_id=message_id,
            rating=payload.rating,
            liked=payload.liked,
            comment=payload.comment,
            source=payload.source,
        )
    )

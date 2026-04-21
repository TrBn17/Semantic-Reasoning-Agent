from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from semantic_reasoning_agent.entrypoints.dependencies import get_chat_stream_service
from semantic_reasoning_agent.schemas.chat import ChatReply, SendMessageRequest
from semantic_reasoning_agent.services.chat_stream_service import ChatStreamService, ProviderNotReadyError
from semantic_reasoning_agent.services.conversation_service import (
    ConversationNotFoundError,
    ConversationPolicyError,
)


router = APIRouter()


@router.post("/messages", response_model=ChatReply, status_code=status.HTTP_201_CREATED)
def send_message(
    payload: SendMessageRequest,
    chat_stream_service: ChatStreamService = Depends(get_chat_stream_service),
) -> ChatReply:
    try:
        return chat_stream_service.send_message(payload)
    except ConversationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ConversationPolicyError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except ProviderNotReadyError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/messages/stream")
def stream_message(
    payload: SendMessageRequest,
    chat_stream_service: ChatStreamService = Depends(get_chat_stream_service),
) -> StreamingResponse:
    return StreamingResponse(
        chat_stream_service.stream_message(payload),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )

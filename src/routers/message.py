import logging
import uuid
from typing import Annotated, AsyncIterable

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from ..dependencies import validate_chat_id
from ..my_logging.logging_config import setup_logging
from ..models.message import MessageDTO, ResponseChunkDTO
from ..services.message import MessageService
from ..services.user import UserService
from ..utils.authentication import CurrentUserDep
from .sse_streamer import async_sse_stream

setup_logging()
debug_logger = logging.getLogger("debug")


router = APIRouter(
    prefix="/users/me/chats/{chat_id}/messages",
    tags=["Messages"],
    # dependencies=[
    #     Depends(validate_chat_id),
    #     Depends(get_current_user),
    # ],
)


@router.get("/", dependencies=[Depends(validate_chat_id)])
async def get_messages(
    chat_id: int,
    message_service: Annotated[MessageService, Depends()],
) -> list[MessageDTO]:
    messages = await message_service.get_by_chat_id(chat_id)
    if messages is None:
        raise HTTPException(status_code=404, detail="Chat not found")
    return messages


@router.post("/", dependencies=[Depends(validate_chat_id)])
async def create_message(
    chat_id: int,
    message: MessageDTO,
    message_service: Annotated[MessageService, Depends()],
) -> dict[str, uuid.UUID | MessageDTO]:
    stream_id, created_message = await message_service.create_message(chat_id, message)

    return {"stream_id": stream_id, "message": created_message}


@router.get("/{message_id}/streams/{stream_id}")
async def generate_answer(
    chat_id: int,
    stream_id: uuid.UUID,
    message_service: Annotated[MessageService, Depends()],
) -> StreamingResponse:
    stream = message_service.create_stream(chat_id, stream_id)
    return StreamingResponse(async_sse_stream(stream), media_type="text/event-stream")


@router.delete("/{message_id}/streams/{stream_id}")
async def stop_streaming(
    stream_id: uuid.UUID,
    message_service: Annotated[MessageService, Depends()],
) -> None:
    await message_service.stop_generation(stream_id)

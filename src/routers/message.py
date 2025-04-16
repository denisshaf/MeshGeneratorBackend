from typing import Annotated

from fastapi import APIRouter, Body, Depends
from fastapi.responses import StreamingResponse

from ..dependencies import CurrentUserDep
from ..services.message import MessageService, get_message_service

router = APIRouter(
    prefix="/chats/{chat_id}/message",
    tags=["Messages"],
)


@router.get("/")
async def get_messages(user: CurrentUserDep, chat_id: int): ...


@router.post("/")
async def create_message(
    user: CurrentUserDep,
    chat_id: int,
    message: Annotated[str, Body()],
):
    user_message = message["content"]
    response = {"chat_id": chat_id, "message": message, "response": f"Echo: {message}"}
    return response


@router.get("/{message_id}/stream")
async def generate_message(
    user: CurrentUserDep,
    message_id: int,
):
    service = get_message_service()
    return StreamingResponse(service.stream_message(stream_id=message_id))


@router.post("/{message_id}/stop-stream")
async def stop_streaming(user: CurrentUserDep, message_id: int):
    service = get_message_service()
    service = MessageService()
    service.stop_streaming()

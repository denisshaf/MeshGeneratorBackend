import logging
from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException, status

from ..dependencies import validate_chat_id
from ..models.chat import ChatDTO
from ..my_logging.logging_config import setup_logging
from ..services.chat import ChatService
from ..utils.authentication import CurrentUserDep

setup_logging()
debug_logger = logging.getLogger("debug")


router = APIRouter(prefix="/users/me/chats", tags=["Chats"])


@router.get("/")
async def get_chats(
    user: CurrentUserDep, service: Annotated[ChatService, Depends()]
) -> list[ChatDTO]:
    user_auth_id = user["sub"]
    chats = await service.get_my_chats(user_auth_id)

    return chats


@router.post("/")
async def create_chat(
    user: CurrentUserDep, service: Annotated[ChatService, Depends()]
) -> ChatDTO:
    try:
        user_auth_id = user["sub"]
        chat = await service.create_my_chat(user_auth_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return chat


@router.patch("/{chat_id}", dependencies=[Depends(validate_chat_id)])
async def update_chat_name(
    chat_id: int,
    chat_name: Annotated[str, Body(alias="title", embed=True)],
    service: Annotated[ChatService, Depends()],
) -> ChatDTO:
    updated_chat = await service.update_chat_name(chat_id, chat_name)
    return updated_chat


@router.delete("/{chat_id}", dependencies=[Depends(validate_chat_id)])
async def delete_chat(
    chat_id: int,
    service: Annotated[ChatService, Depends()],
) -> None:
    await service.delete_chat(chat_id)

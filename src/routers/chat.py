import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from ..logging.logging_config import setup_logging
from ..utils.authentication import CurrentUserDep
from ..services.chat import ChatService
from ..models.chat import ChatDTO

setup_logging()
debug_logger = logging.getLogger("debug")


router = APIRouter(prefix="/users/me/chats", tags=["Chats"])


@router.get("/")
async def get_chats(user: CurrentUserDep, service: Annotated[ChatService, Depends()]) -> list[ChatDTO]:
    user_auth_id = user["sub"]
    chats = await service.get_my_chats(user_auth_id)

    debug_logger.debug(f"Chats {chats}")

    return chats


@router.post("/")
async def create_chat(user: CurrentUserDep, service: Annotated[ChatService, Depends()]) -> ChatDTO:
    try:
        user_auth_id = user["sub"]
        chat = await service.create_my_chat(user_auth_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return chat

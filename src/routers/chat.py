import logging
from typing import Annotated

from fastapi import APIRouter, Body, Depends

from ..config.logging_config import setup_logging
from ..dependencies import CurrentUserDep

setup_logging()
debug_logger = logging.getLogger("debug")

router = APIRouter(prefix="/chats", tags=["Chats"])


@router.post("/")
async def create_chat(user: CurrentUserDep): ...


@router.get("/")
async def get_chats(user: CurrentUserDep): ...

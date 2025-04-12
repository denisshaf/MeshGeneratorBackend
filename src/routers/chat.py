from typing import Annotated
import logging
from fastapi import APIRouter, Body, Depends

from ..utils.authentication import get_current_user
from ..config.logging_config import setup_logging


setup_logging()
debug_logger = logging.getLogger('debug')

router = APIRouter(
    prefix='/api/chats',
    tags=['Chat']
)

@router.post('/{chat_id}/message')
def receive_message(chat_id: int, message: Annotated[str, Body()], user=Depends(get_current_user)):
    debug_logger.debug(f"Received message for chat_id {chat_id}: {message}")
    debug_logger.debug(f"User: {user}")
    response = {
        "chat_id": chat_id,
        "message": message,
        "response": f"Echo: {message}"
    }
    return response

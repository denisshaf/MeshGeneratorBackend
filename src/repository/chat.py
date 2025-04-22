import logging
from typing import Annotated

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..logging.logging_config import setup_logging
from ..db import get_db_session
from ..models.chat import ChatDAO, ChatDTO
from ..models.user import UserDAO


setup_logging()
debug_logger = logging.getLogger("debug")


class AsyncChatRepository:
    def __init__(self, db_session: Annotated[AsyncSession, Depends(get_db_session)]):
        self._db_session = db_session

    async def get_by_user_id(self, user_id: int) -> list[ChatDTO]:
        query = select(ChatDAO).where(ChatDAO.user_id == user_id)
        result = await self._db_session.execute(query)
        chats = result.scalars().all()
        
        return [ChatDTO.model_validate(chat) for chat in chats]
    
    async def get_by_id(self, chat_id: int) -> ChatDTO | None:
        query = select(ChatDAO).where(ChatDAO.id == chat_id)
        result = await self._db_session.execute(query)
        chat = result.scalars().first()

        if not chat:
            return None

        return ChatDTO.model_validate(chat)
    
    async def create_by_user_id(self, user_id: int) -> ChatDTO:
        user_query = select(UserDAO).where(UserDAO.id == user_id)
        result = await self._db_session.execute(user_query)
        user = result.scalars().first()

        if not user:
            raise ValueError("User not found")
        
        new_chat = ChatDAO(user_id=user.id)

        self._db_session.add(new_chat)
        await self._db_session.commit()

        await self._db_session.refresh(new_chat)

        return ChatDTO.model_validate(new_chat)
        


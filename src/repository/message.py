import logging
from typing import Annotated

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from ..db import get_db_session
from ..my_logging.logging_config import setup_logging
from ..models.chat_role import ChatRoleDAO
from ..models.message import MessageDAO, MessageDTO
from ..models.model import ModelDTO

setup_logging() 
debug_logger = logging.getLogger("debug")


class AsyncMessageRepository:
    def __init__(self, db_session: Annotated[AsyncSession, Depends(get_db_session)]):
        self._db_session = db_session

    async def create(self, chat_id: int, message: MessageDTO) -> MessageDTO:
        role_query = select(ChatRoleDAO).where(ChatRoleDAO.name == message.role)
        role_result = await self._db_session.execute(role_query)
        role = role_result.scalar_one_or_none()

        if not role:
            raise ValueError(f"Invalide role: {message.role}")

        new_message = MessageDAO(
            content=message.content,
            role_id=role.id,
            chat_id=chat_id,
        )

        self._db_session.add(new_message)
        debug_logger.debug(f'added message: {new_message}')
        await self._db_session.commit()
        debug_logger.debug(f'commited message: {new_message}')
        await self._db_session.refresh(new_message)
        debug_logger.debug(f'refreshed message: {new_message}')

        message_dto = MessageDTO(
            id=new_message.id,
            content=new_message.content,
            chat_id=new_message.chat_id,
            created_at=new_message.created_at,
            role=role.name,
        )

        return message_dto

    async def get_by_chat_id(self, chat_id: int) -> list[MessageDTO]:
        query = (
            select(MessageDAO)
            .options(joinedload(MessageDAO.role))
            .where(MessageDAO.chat_id == chat_id)
            .options(selectinload(MessageDAO.models))
        )

        result = await self._db_session.execute(query)
        messages = result.scalars().all()

        messages_dto = [
            MessageDTO(
                id=message.id,
                content=message.content,
                role=message.role.name,
                created_at=message.created_at,
                chat_id=message.chat_id,
                models=[
                    ModelDTO.model_validate(model)
                    for model in message.models
                ],
            )
            for message in messages
        ]

        return messages_dto

    async def update(self, message: MessageDTO) -> MessageDTO: ...  # type: ignore
    async def delete(self, user_id: str) -> bool: ...  # type: ignore

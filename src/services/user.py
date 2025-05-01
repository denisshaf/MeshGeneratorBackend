import logging
from typing import Annotated

from fastapi import Depends

from ..my_logging.logging_config import setup_logging
from ..models.user import UserDTO
from ..repository.chat import AsyncChatRepository
from ..repository.user import AsyncUserRepository


class UserService:
    def __init__(
        self,
        user_repository: Annotated[AsyncUserRepository, Depends()],
        chat_repository: Annotated[AsyncChatRepository, Depends()],
    ):
        self._user_repository = user_repository
        self._chat_repository = chat_repository

    async def get_user(self, id: str) -> UserDTO | None:
        user = await self._user_repository.get_by_auth_id(id)
        return user

    async def create_user(self, user: UserDTO) -> UserDTO:
        created_user = await self._user_repository.create(user)
        return created_user

    async def is_chat_owner(self, user_id: str, chat_id: int) -> bool:
        user = await self._user_repository.get_by_auth_id(user_id)
        if not user:
            return False

        chat = await self._chat_repository.get_by_id(chat_id)
        if not chat:
            return False

        return chat.user_id == user.id

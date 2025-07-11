from typing import Annotated

from fastapi import Depends

from ..models.chat import ChatDTO
from ..repository.chat import AsyncChatRepository
from ..repository.user import AsyncUserRepository


class ChatService:
    def __init__(
        self,
        chat_repository: Annotated[AsyncChatRepository, Depends()],
        user_repository: Annotated[AsyncUserRepository, Depends()],
    ):
        self._chat_repository = chat_repository
        self._user_repository = user_repository

    async def get_my_chats(self, auth_id: str) -> list[ChatDTO]:
        user = await self._user_repository.get_by_auth_id(auth_id)

        if not user:
            raise ValueError("User not found")

        assert user.id

        chats = await self._chat_repository.get_by_user_id(user.id)
        return chats

    async def create_my_chat(self, auth_id: str) -> ChatDTO:
        user = await self._user_repository.get_by_auth_id(auth_id)

        if not user:
            raise ValueError("User not found")

        assert user.id

        created_chat = await self._chat_repository.create_by_user_id(user.id)

        return created_chat

    async def update_chat_name(self, chat_id: int, name: str) -> ChatDTO:
        updated_chat = await self._chat_repository.update_name(chat_id, name)
        return updated_chat

    async def delete_chat(self, chat_id: int) -> None:
        await self._chat_repository.delete_chat(chat_id)

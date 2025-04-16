import logging
from typing import Annotated

from fastapi import Depends

from ..config.logging_config import setup_logging
from ..models.user import UserDTO
from ..repository.repository import IAsyncRepository
from ..repository.user import AsyncUserRepository

setup_logging()
debug_logger = logging.getLogger("debug")


class UserService:
    def __init__(
        self, repository: Annotated[IAsyncRepository, Depends(AsyncUserRepository)]
    ):
        self._repository = repository

    async def get_user(self, id: str) -> UserDTO | None:
        debug_logger.debug(f"get_user {id=}")
        user = await self._repository.get(id)
        return user

    async def create_user(self, user: UserDTO) -> UserDTO:
        created_user = await self._repository.create(user)
        return created_user

import logging
from typing import Annotated

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config.logging_config import setup_logging
from ..dependencies import get_db_session
from ..models.user import UserDAO, UserDTO
from .repository import IAsyncRepository

setup_logging()
debug_logger = logging.getLogger("debug")


class AsyncUserRepository(IAsyncRepository):
    def __init__(self, db_session: Annotated[AsyncSession, Depends(get_db_session)]):
        self._db_session = db_session

    async def create(self, user: UserDTO) -> UserDTO:
        user_dao = UserDAO(name=user.name, auth_id=user.auth_id, email=user.email)
        self._db_session.add(user_dao)

        debug_logger.debug(f"Adding user: {user_dao}")

        await self._db_session.commit()

        await self._db_session.refresh(user_dao)

        debug_logger.debug(f"Created user: {user_dao}")

        return UserDTO.model_validate(user_dao)

    async def get(self, auth_id: str) -> UserDTO | None:
        query = select(UserDAO).where(UserDAO.auth_id == auth_id)
        result = await self._db_session.execute(query)
        user_dao = result.scalars().first()

        if not user_dao:
            return None

        return UserDTO.model_validate(user_dao)

    async def update(self, user: UserDTO) -> UserDTO | None:
        query = select(UserDAO).where(UserDAO.auth_id == user.auth_id)
        result = await self._db_session.execute(query)
        user_dao = result.scalars().first()

        if not user_dao:
            return None

        if user.name is not None:
            user_dao.name = user.name
        if user.email is not None:
            user_dao.email = user.email

        await self._db_session.commit()

        await self._db_session.refresh(user_dao)

        return UserDTO.model_validate(user_dao)

    async def delete(self, auth_id: int) -> bool:
        query = select(UserDAO).where(UserDAO.auth_id == auth_id)
        result = await self._db_session.execute(query)
        user_dao = result.scalars().first()

        if not user_dao:
            return False

        await self._db_session.delete(user_dao)

        await self._db_session.commit()

        return True

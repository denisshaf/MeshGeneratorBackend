from typing import (
    Annotated, AnyStr, AsyncGenerator, Awaitable, BinaryIO, Generator,
    SupportsIndex, TypeAlias
)

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from .db import AsyncSessionFactory
from .utils.authentication import get_current_user


async def get_db_session() -> AsyncGenerator[AsyncSession]:
    async with AsyncSessionFactory() as session:
        yield session


SessionDependency: TypeAlias = Annotated[AsyncSession, Depends(get_db_session)]
CurrentUserDep: TypeAlias = Annotated[dict[str, str], Depends(get_current_user)]

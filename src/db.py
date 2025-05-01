import logging
import re
from pathlib import Path
from typing import Annotated, TypeAlias, cast

import yaml
from dotenv import dotenv_values
from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import (
    AsyncSession, async_sessionmaker, create_async_engine
)
from starlette.middleware.base import BaseHTTPMiddleware

env = dotenv_values()


debug_logger = logging.getLogger("debug")


__location__ = Path(__file__).resolve().parent
with open(__location__ / "config.yaml") as file:
    db_config = yaml.safe_load(file)["database"]

user = env["POSTGRES_USER"]
password = env["POSTGRES_PASSWORD"]
host = db_config["host"]
port = db_config["port"]
database = db_config["database"]

_engine = create_async_engine(
    f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{database}", echo=False
)

AsyncSessionFactory = async_sessionmaker(bind=_engine, expire_on_commit=False)


class DBSessionMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, no_session_close_paths: list[str] | None = None) -> None:  # type: ignore
        super().__init__(app)
        self.no_session_close_paths = no_session_close_paths or []

    async def dispatch(self, request: Request, call_next):  # type: ignore
        request.state.db_session_factory = AsyncSessionFactory
        request.state.active_session = None

        response = await call_next(request)

        path = request.url.path
        if (
            not any(
                re.match(excluded, path) for excluded in self.no_session_close_paths
            )
            and request.state.active_session
        ):
            await request.state.active_session.close()
        return response


async def get_db_session(request: Request) -> AsyncSession:
    if hasattr(request.state, "active_session") and request.state.active_session:
        session = request.state.active_session
    elif hasattr(request.state, "db_session_factory"):
        request.state.active_session = request.state.db_session_factory()
        session = request.state.active_session
    else:
        session = AsyncSessionFactory()
    return cast(AsyncSession, session)


SessionDependency: TypeAlias = Annotated[AsyncSession, Depends(get_db_session)]

from pathlib import Path
from typing import Annotated, AsyncGenerator, TypeAlias

import yaml
from dotenv import dotenv_values
from fastapi import Depends
from sqlalchemy.ext.asyncio import (
    AsyncSession, async_sessionmaker, create_async_engine
)

env = dotenv_values()

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


async def get_db_session() -> AsyncGenerator[AsyncSession]:
    async with AsyncSessionFactory() as session:
        yield session


SessionDependency: TypeAlias = Annotated[AsyncSession, Depends(get_db_session)]

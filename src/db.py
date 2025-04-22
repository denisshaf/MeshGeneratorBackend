from typing import AsyncGenerator, TypeAlias, Annotated
from pathlib import Path

import yaml
from dotenv import dotenv_values
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine, AsyncSession
from fastapi import Depends

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
    f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{database}"
)

AsyncSessionFactory = async_sessionmaker(bind=_engine, expire_on_commit=False)


async def get_db_session() -> AsyncGenerator[AsyncSession]:
    async with AsyncSessionFactory() as session:
        yield session


SessionDependency: TypeAlias = Annotated[AsyncSession, Depends(get_db_session)]

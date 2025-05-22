import logging
import re
from contextlib import asynccontextmanager
from typing import AsyncGenerator
import yaml
from dotenv import dotenv_values

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.assistant.assistant_runner import AsyncProcessAssistantRunner
from src.repository.db import setup_db_engine, DBSessionMiddleware
from src.my_logging.logging_config import setup_logging
from src.my_logging.logging_middleware import LoggingMiddleware
from src.routers import chat, message, model, user
from src.services.message import MessageService

setup_logging()
logger = logging.getLogger("app")
debug_logger = logging.getLogger("debug")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    with open("src/config.yaml") as file:
        config = yaml.safe_load(file)
        max_workers = config["assistant"]["max_workers"]
        implementation = config["assistant"]["implementation"]

        db_config = config["database"]
        host = db_config["host"]
        port = db_config["port"]
        database = db_config["database"]

    env = dotenv_values()
    user = env["POSTGRES_USER"]
    password = env["POSTGRES_PASSWORD"]

    assert user and password
     
    setup_db_engine(user, password, host, port, database)
    
    debug_logger.debug(f'{max_workers=}')
    debug_logger.debug(f'{implementation=}')
    MessageService.set_max_workers(max_workers)
    MessageService.set_assistant_implementation(implementation)

    yield
    
    MessageService.shutdown()


app = FastAPI(lifespan=lifespan)
api_router = APIRouter(prefix="/api")

api_router.include_router(user.router)
api_router.include_router(chat.router)
api_router.include_router(message.router)
api_router.include_router(model.router)

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://localhost:\d+",
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["Content-Type", "Authorization"],
)
app.add_middleware(
    DBSessionMiddleware,
    no_session_close_paths=[
        re.compile(r".*?/users/me/chats/[^/]+/messages/[^/]+/streams/[^/]+")
    ],
)
app.add_middleware(LoggingMiddleware, excluded_paths=["/streams"])

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

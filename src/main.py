import logging
import re
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.assistant.assistant_runner import AsyncProcessAssistantRunner
from src.db import DBSessionMiddleware
from src.my_logging.logging_config import setup_logging
from src.my_logging.logging_middleware import LoggingMiddleware
from src.routers import chat, message, model, user

setup_logging()
logger = logging.getLogger("app")
debug_logger = logging.getLogger("debug")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    process_runner = AsyncProcessAssistantRunner()
    yield
    process_runner.shutdown()


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

import logging

from fastapi import APIRouter, Body, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.logging.logging_config import setup_logging
from src.logging.logging_middleware import LoggingMiddleware
from src.routers import chat, message, user

# from llama_cpp import Llama


setup_logging()
logger = logging.getLogger("app")
debug_logger = logging.getLogger("debug")


app = FastAPI()
api_router = APIRouter(prefix="/api")

api_router.include_router(user.router)
api_router.include_router(chat.router)
api_router.include_router(message.router)

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://localhost:\d+",
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["Content-Type", "Authorization"],
)
# app.add_middleware(LoggingMiddleware, excluded_paths=["/streams"])

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

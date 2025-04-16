import logging

from fastapi import APIRouter, Body, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config.logging_config import setup_logging
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

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# from typing import Annotated, Generator
# from fastapi import Depends


# def get_db_session() -> Generator[str, None, None]:
#     try:
#         debug_logger.debug('yield db_session')
#         yield 'db_session'
#     finally:
#         debug_logger.debug('Clean up code')

# class Repository:
#     def __init__(self, db_session: Annotated[str, Depends(get_db_session)]):
#         debug_logger.debug('init repository')
#         self.db_session = db_session

#     def foo(self):
#         debug_logger.debug(f'do smth with {self.db_session!r}')

# class Service:
#     def __init__(self, repository: Annotated[Repository, Depends()]):
#         debug_logger.debug('init service')
#         self.repository = repository

#     def foo(self):
#         debug_logger.debug(f'do smth with {self.repository!r}')
#         self.repository.foo()

# @app.get('/')
# def test(service: Annotated[Service, Depends()]):
#     debug_logger.debug('Hello from router')
#     service.foo()
#     return {'answer': 'all good'}

from pathlib import Path
import logging
import sys

from fastapi import FastAPI, Body
from fastapi.middleware.cors import CORSMiddleware
# from llama_cpp import Llama

from .config.logging_config import setup_logging

from .llama import LlamaMock as Llama
from .chat_model import ChatAssistant
from .routers import chat, user

setup_logging()
logger = logging.getLogger('app')
debug_logger = logging.getLogger('debug')

app = FastAPI()
app.include_router(user.router)
app.include_router(chat.router)
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

llm = Llama(
      model_path=Path("~/LLaMA-Mesh/LLaMA-Mesh.gguf").expanduser(),
      n_ctx=4096,
      n_threads=12
)
chat_assistant = ChatAssistant(llm=llm)

@app.post('/')
def get_assistant_response(chat_id: int, message: dict = Body(...)):
    user_message = message['content']
    chat_assistant.add_user_message(user_message)

    logger.info('request came')

    response = chat_assistant.get_response(stream=True)

    answer = []
    for chunk in response:
        delta = chunk['choices'][0]['delta']
        
        if 'role' in delta:
            answer.append(delta['role'] + ': ')
        elif 'content' in delta:
            answer.append(delta['content'])

        if 'role' in delta:
            debug_logger.debug(delta['role'])
        elif 'content' in delta:
            debug_logger.debug(delta['content'])

    answer = ''.join(answer)
    chat_assistant.add_assistant_message(answer)

    logger.info('request sent')

    return {"text": answer}
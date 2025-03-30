from pathlib import Path
import logging
import sys

from fastapi import FastAPI, Body
from llama_cpp import Llama

from config.logging_config import setup_logging


setup_logging()
logger = logging.getLogger('app')

app = FastAPI()

chat_history = []
llm = Llama(
      model_path=Path("~/LLaMA-Mesh/LLaMA-Mesh.gguf").expanduser(),
      n_ctx=4096,
      n_threads=12
)

@app.post('/api/chats/{chat_id}/message')
def root(chat_id: int, message: dict = Body(...)):
    ...
    user_message = message['content']
    chat_history.append({'role': 'user', 'content': user_message})

    logger.info('request came')

    response = llm.create_chat_completion(
        messages=chat_history,
        temperature=0.7,
        stream=True
    )

    answer = []
    for chunk in response:
        delta = chunk['choices'][0]['delta']
        
        if 'role' in delta:
            answer.append(delta['role'] + ': ')
        if 'content' in delta:
            answer.append(delta['content'])

        if 'role' in delta:
            print(delta['role'], end=': ')
        elif 'content' in delta:
            print(delta['content'], end='')
        else:
            print()

        sys.stdout.flush()

    answer = ''.join(answer)
    # print(answer)

    # model_response = response['choices'][0]['message']['content']
    # chat_history.append({'role': 'assistant', 'content': model_response})

    logger.info('request sent')

    return {"text": answer}
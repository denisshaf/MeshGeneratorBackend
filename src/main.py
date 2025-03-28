import os.path as osp

from fastapi import FastAPI, Body
from llama_cpp import Llama

app = FastAPI()

chat_history = []
llm = Llama(
      model_path=osp.expanduser("~/LLaMA-Mesh/LLaMA-Mesh.gguf"),
      n_ctx=4096,
      n_threads=12
)

@app.post('/api/chats/{chat_id}/message')
def root(chat_id: int, message: dict = Body(...)):
    user_message = message['content']
    chat_history.append({'role': 'user', 'content': user_message})

    print('request came')

    response = llm.create_chat_completion(
        messages=chat_history,
        temperature=0.7,
        stream=True
    )
    # print(response)

    answer = []
    for chunk in response:
        delta = chunk['choices'][0]['delta']
        # print('----')
        # print(delta)
        # print('----')
        # print('role' in delta)
        # print('content' in delta)
        
        if 'role' in delta:
            answer.append(delta['role'] + ': ')
        if 'content' in delta:
            answer.append(delta['content'])
        # if 'role' in delta:
        #     print(delta['role'], end=': ')
        # elif 'content' in delta:
        #     print(delta['content'], end='')
        print(''.join(answer))

    answer = ''.join(answer)
    # print(answer)

    # model_response = response['choices'][0]['message']['content']
    # chat_history.append({'role': 'assistant', 'content': model_response})

    print('request sent')
    print('------------')

    return {"text": answer}
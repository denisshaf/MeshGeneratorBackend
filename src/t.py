from pathlib import Path
from typing import TypedDict

from llama_cpp import Llama


class ResponseChunkDTO(TypedDict):
    role: str
    content: str


model_path = Path("~/LLaMA-Mesh/LLaMA-Mesh.gguf").expanduser()
llm = Llama(model_path=str(model_path), n_ctx=4096, n_threads=12, verbose=False)

message_history = [ResponseChunkDTO(role="user", content="Hi")]

temperature = 0.7
gen = llm.create_chat_completion(
    messages=message_history, temperature=temperature, stream=True
)
for chunk in gen:
    print(chunk)
print()
print()
print()
print()
print()
print()
gen = llm.create_chat_completion(
    messages=message_history, temperature=temperature, stream=True
)
for chunk in gen:
    print(chunk)
for chunk in gen:
    print(chunk)

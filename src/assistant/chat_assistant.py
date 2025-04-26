from typing import Any, Generator

from ..models.message import ResponseChunkDTO
from .chat_protocol import HasChatCompletition


class ChatAssistant:
    llm: HasChatCompletition
    _chat_history: list[ResponseChunkDTO] = []
    temperature: float

    def __init__(self, llm: HasChatCompletition) -> None:
        self.llm = llm
        self.temperature = 0.7

    def generate_response(
        self, chat_history: list[ResponseChunkDTO]
    ) -> Generator[ResponseChunkDTO]:
        gen = self.llm.create_chat_completion(
            messages=chat_history, temperature=self.temperature, stream=True
        )

        role: str
        for chunk in gen:
            delta: dict = chunk["choices"][0]["delta"]

            if "role" in delta:
                role = delta["role"]
                continue

            content = delta.get("content", "EOS")
            response_chunk = ResponseChunkDTO(role=role, content=content)
            yield response_chunk


class MockChatAssistant(ChatAssistant):
    def generate_response(
        self, chat_history: list[ResponseChunkDTO]
    ) -> Generator[ResponseChunkDTO]:
        import time

        for i in range(100):
            response_chunk = ResponseChunkDTO(role="assistant", content=str(i) + " ")
            time.sleep(1)
            yield response_chunk

class ObjChatAssistant(ChatAssistant):
    def generate_response(
        self, chat_history: list[ResponseChunkDTO] 
    ) -> Generator[ResponseChunkDTO]:
        import time

        tokens = [
            '```', 'obj', '\n',
            '#', ' ', 'Simple', ' ', 'OBJ', ' ', 'file', '\n', 
            '#', ' ', 'Vertices', '\n', 
            'v', ' ', '-', '1.0', ' ', '-', '1.0', ' ', '-', '1.0', '\n', 
            'v', ' ', '1.0', ' ', '-', '1.0', ' ', '-', '1.0', '\n', 
            'v', ' ', '1.0', ' ', '1.0', ' ', '-', '1.0', '\n', 
            'v', ' ', '-', '1.0', ' ', '1.0', ' ', '-', '1.0', '\n', 
            'v', ' ', '-', '1.0', ' ', '-', '1.0', ' ', '1.0', '\n', 
            'v', ' ', '1.0', ' ', '-', '1.0', ' ', '1.0', '\n', 
            'v', ' ', '1.0', ' ', '1.0', ' ', '1.0', '\n', 
            'v', ' ', '-', '1.0', ' ', '1.0', ' ', '1.0', '\n', 
            '\n', 
            '#', ' ', 'Faces', '\n', 
            'f', ' ', '1', ' ', '2', ' ', '3', ' ', '4', '\n', 
            'f', ' ', '5', ' ', '6', ' ', '7', ' ', '8', '\n', 
            'f', ' ', '1', ' ', '5', ' ', '8', ' ', '4', '\n', 
            'f', ' ', '2', ' ', '6', ' ', '7', ' ', '3', '\n', 
            'f', ' ', '1', ' ', '2', ' ', '6', ' ', '5', '\n', 
            'f', ' ', '4', ' ', '3', ' ', '7', ' ', '8', '\n',
            '```' '\n',
        ]
        
        for token in tokens:
            response_chunk = ResponseChunkDTO(role="assistant", content=token)
            time.sleep(0.01)
            yield response_chunk

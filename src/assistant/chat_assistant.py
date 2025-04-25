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

from typing import override, cast
from abc import ABC, abstractmethod
from collections.abc import Iterable, Generator
from pathlib import Path

from llama_cpp import Llama

from ..models.message import ResponseChunkDTO, MessageRole
from .chat_protocol import HasChatCompletion
from .llama import LlamaMock


class ChatAssistant(ABC):
    @abstractmethod
    def generate_response(self, chat_history: list[ResponseChunkDTO]) -> Iterable[ResponseChunkDTO]: ...


class LLMChatAssistant(ChatAssistant):
    _llm: HasChatCompletion
    _temperature: float

    @override
    def __init__(self) -> None:
        self._temperature = 0.7
        self._llm = self.initialize_llm()

    @override
    def generate_response(self, chat_history: list[ResponseChunkDTO]) -> Generator[ResponseChunkDTO]:
        gen = self._llm.create_chat_completion(
            messages=chat_history, temperature=self._temperature, stream=True
        )

        role: MessageRole
        for chunk in gen:
            delta: dict = chunk["choices"][0]["delta"]

            if "role" in delta:
                role = delta["role"]
                continue

            content = delta.get("content", "EOS")
            response_chunk = ResponseChunkDTO(role=role, content=content)
            yield response_chunk

    @abstractmethod
    def initialize_llm(self) -> HasChatCompletion: ...


class LlamaChatAssistant(LLMChatAssistant):
    @override
    def initialize_llm(self) -> HasChatCompletion:
        model_path = Path("~/LLaMA-Mesh/LLaMA-Mesh.gguf").expanduser()
        llm = Llama(
            model_path=str(model_path),
            n_ctx=4096,
            n_threads=12,
            verbose=False,
        )
        return cast(HasChatCompletion, llm)


class LlamaMockChatAssistant(LLMChatAssistant):
    @override
    def initialize_llm(self) -> HasChatCompletion:
        return LlamaMock()


class MockChatAssistant(ChatAssistant):
    @override
    def generate_response(
        self, chat_history: list[ResponseChunkDTO]
    ) -> Generator[ResponseChunkDTO]:
        import time

        for i in range(100):
            response_chunk = ResponseChunkDTO(role="assistant", content=str(i) + " ")
            time.sleep(1)
            yield response_chunk


class ObjChatAssistant(ChatAssistant):
    @override
    def generate_response(
        self, chat_history: list[ResponseChunkDTO]
    ) -> Generator[ResponseChunkDTO]:
        import time

        tokens = [
            'here ', 'is', ' ', 'your ', 'obj', ' ', 'model:', '\n',
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
            'f', ' ', '4', ' ', '3', ' ', '7', ' ', '8', '\n'
            '```', '\n',
            'are ', 'you ', 'satisfied', '?'
        ]

        for token in tokens:
            response_chunk = ResponseChunkDTO(role="assistant", content=token)
            time.sleep(0.01)
            yield response_chunk

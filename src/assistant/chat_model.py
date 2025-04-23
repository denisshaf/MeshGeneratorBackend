from typing import Generator

from .chat_protocol import HasChatCompletition
from ..models.message import ResponseChunkDTO


class ChatAssistant:
    llm: HasChatCompletition
    chat_history: list[ResponseChunkDTO]
    temperature: float

    def __init__(self, llm: HasChatCompletition) -> None:
        self.llm = llm
        self.chat_history = []
        self.temperature = 0.7

    # def add_user_message(self, message: str):
    #     self.chat_history.append({"role": "user", "content": message})

    # def add_assistant_message(self, message: str):
    #     self.chat_history.append({"role": "assistant", "content": message})

    def generate_response(self) -> Generator:
        response = self.llm.create_chat_completion(
            messages=self.chat_history, temperature=self.temperature, stream=True
        )

        return response

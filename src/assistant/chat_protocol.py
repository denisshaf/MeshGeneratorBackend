from typing import Protocol, Any


class HasChatCompletition(Protocol):
    def create_chat_completion(self, messages: list[Any], temperature: float, stream: bool = False,) -> Any: ...
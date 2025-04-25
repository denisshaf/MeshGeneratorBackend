from typing import Any, Protocol


class HasChatCompletition(Protocol):
    def create_chat_completion(
        self,
        messages: list[Any],
        temperature: float,
        stream: bool = False,
        *args: Any,
        **kwargs: Any
    ) -> Any:
        ...

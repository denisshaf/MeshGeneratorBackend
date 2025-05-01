from collections.abc import Iterable
from typing import Any, Protocol

from ..models.message import ResponseChunkDTO


class HasChatCompletion(Protocol):
    def create_chat_completion(
        self,
        messages: list[ResponseChunkDTO],
        temperature: float = ...,
        stream: bool = ...,
        *args: Any,
        **kwargs: Any
    ) -> Iterable[dict]: ...

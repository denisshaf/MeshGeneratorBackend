import time
from collections.abc import Generator, Iterable
from typing import Any, Literal, overload

from .chat_protocol import HasChatCompletion


class LlamaMock(HasChatCompletion):
    MESSAGE = {"role": "assistant", "content": "Hello! How can I help you today?"}

    def __init__(self, *args: Any, **kwargs: Any) -> None: ...

    def _chat_completion_generator(self) -> Generator[dict, None, None]:
        yield {"choices": [{"delta": {"role": "assistant"}}]}
        content = self.MESSAGE["content"]
        for word in content.split():
            yield {"choices": [{"delta": {"content": word + " "}}]}
            time.sleep(1)

    @overload  # type: ignore
    def create_chat_completion(
        self,
        messages: list[Any],
        temperature: float = ...,
        stream: Literal[True] = ...,
    ) -> Generator[dict]: ...

    @overload
    def create_chat_completion(
        self,
        messages: list[Any],
        temperature: float = ...,
        stream: Literal[False] = ...,
    ) -> list[dict]: ...

    def create_chat_completion(
        self,
        messages: list[Any],
        temperature: float = 0.2,
        stream: bool = False,
    ) -> Iterable[dict]:
        if not stream:
            return [
                {"choices": [{"delta": {"role": "assistant"}}]},
                {
                    "choices": [
                        {"delta": {"content": "Hello! How can I help you today?"}}
                    ]
                },
            ]

        return self._chat_completion_generator()

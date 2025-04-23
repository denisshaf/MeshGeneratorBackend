from pathlib import Path
from typing import override

from .chat_model import ChatAssistant
from .llama import LlamaMock as Llama
from .object_pool import AbstractPool


class AssistantPool(AbstractPool[ChatAssistant]):
    def __init__(self, max_count: int = 1):
        super().__init__(max_count)

    def _add_assistant(self) -> None:
        llm = Llama(
            model_path=Path("~/LLaMA-Mesh/LLaMA-Mesh.gguf").expanduser(),
            n_ctx=4096,
            n_threads=12,
        )

        chat_assistant = ChatAssistant(llm=llm)
        self._instances.append(chat_assistant)

    @override
    def get_instance(self) -> ChatAssistant:
        if len(self._instances) < self._max_count:
            self._add_assistant()

    @override
    def release(self, instance: ChatAssistant) -> None: ...

from dataclasses import dataclass
from typing import AsyncGenerator, AsyncIterator, TypeAlias
import json
import logging
from enum import EnumType

from .models.message import ResponseChunkDTO
from .logging.logging_config import setup_logging


setup_logging()
debug_logger = logging.getLogger('debug')


AsyncResponseGenerator: TypeAlias = AsyncGenerator[ResponseChunkDTO, None]


class CancellGeneratorEnum(EnumType):
    CANCELLATION_TOKEN = 1


@dataclass
class Stream:
    chat_id: int
    message_id: int
    generator: AsyncResponseGenerator | None = None

    async def aclose(self) -> None:
        if not self.generator:
            raise ValueError("Generator is not provided")
        await self.generator.aclose()

    def __aiter__(self) -> AsyncIterator[ResponseChunkDTO]:
        if not self.generator:
            raise ValueError("Generator is not provided")
        
        return aiter(self.generator)

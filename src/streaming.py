import logging
from dataclasses import dataclass
from typing import AsyncGenerator, AsyncIterator, TypeAlias

from .my_logging.logging_config import setup_logging
from .models.message import ResponseChunkDTO

setup_logging()
debug_logger = logging.getLogger("debug")


AsyncResponseGenerator: TypeAlias = AsyncGenerator[ResponseChunkDTO, None]


@dataclass
class Stream:
    chat_id: int
    message_id: int
    is_running: bool = False
    generator: AsyncResponseGenerator | None = None

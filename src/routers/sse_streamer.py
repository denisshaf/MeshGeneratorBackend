from typing import NamedTuple, Any
from collections.abc import AsyncIterable, AsyncGenerator
import json


class ServerSentEvent(NamedTuple):
    event: str = ''
    data: Any = ''


async def async_sse_stream(stream: AsyncIterable[ServerSentEvent]) -> AsyncGenerator[str]:
    async for event in stream:
        yield f"event: {event.event}\ndata: {json.dumps(event.data)}\n\n"

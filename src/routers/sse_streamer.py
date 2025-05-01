import json
from collections.abc import AsyncGenerator, AsyncIterable
from typing import Any, NamedTuple


class ServerSentEvent(NamedTuple):
    event: str = ""
    data: Any = ""


async def async_sse_stream(
    stream: AsyncIterable[ServerSentEvent],
) -> AsyncGenerator[str]:
    async for event in stream:
        yield f"event: {event.event}\ndata: {json.dumps(event.data)}\n\n"

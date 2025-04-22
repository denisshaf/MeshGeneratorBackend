from pathlib import Path
from typing import AsyncGenerator, Generator
import uuid
from typing import Annotated, ClassVar
import logging
import json

from fastapi import Depends

from ..assistant.assistant_pool import AssistantPool
from ..assistant.chat_model import ChatAssistant
from ..models.message import MessageDTO, ResponseChunkDTO
from ..repository.message import AsyncMessageRepository
from ..streaming import Stream, AsyncResponseGenerator
from ..logging.logging_config import setup_logging


setup_logging()
debug_logger = logging.getLogger('debug')


class MessageService:
    _stream_pool: ClassVar[dict[uuid.UUID, Stream]] = dict()

    def __init__(
        self, message_repository: Annotated[AsyncMessageRepository, Depends()]
    ):
        self._message_repository = message_repository

    async def get_by_chat_id(self, chat_id: int) -> list[MessageDTO]:
        messages = await self._message_repository.get_by_chat_id(chat_id)
        return messages

    async def create_message(
        self, chat_id: int, message: MessageDTO
    ) -> tuple[uuid.UUID, MessageDTO]:
        message = await self._message_repository.create(chat_id, message)

        assert message.id

        stream_id = uuid.uuid4()
        self._stream_pool[stream_id] = Stream(chat_id, message.id)
        # chat_assistant.add_user_message(user_message)

        return stream_id, message

    async def _stream_message(self) -> AsyncResponseGenerator:
        assistant_pool = AssistantPool.get_pool()
        chat_assistant: ChatAssistant = assistant_pool.get_instance()

        try:
            gen = chat_assistant.generate_response()

            role: str
            answer_list = []
            for chunk in gen:
                delta: dict = chunk["choices"][0]["delta"]

                if "role" in delta:
                    role = delta["role"]
                    continue

                content = delta.get("content", "EOS")
                answer_list.append(content)
                response_chunk = ResponseChunkDTO(role=role, content=content)
                yield response_chunk
        finally:
            assistant_pool.release(chat_assistant)

        answer = "".join(answer_list)
        message = MessageDTO()
        await self._chat_repository.add(message)
        # chat_assistant.add_assistant_message(answer)

    async def _stream_message_mock(self) -> AsyncGenerator[ResponseChunkDTO, None]:
        import asyncio

        for i in range(10):
            response_chunk = ResponseChunkDTO(role="assistant", content=str(i))
            await asyncio.sleep(1)
            yield response_chunk

    async def create_stream(self, stream_id: uuid.UUID) -> AsyncGenerator[str]:
        if stream_id not in self._stream_pool:
            raise ValueError("Stream not found")

        stream = self._stream_pool[stream_id]
        stream.generator = self._stream_message_mock()

        # TODO: need to abstract the SSE message format from the MessageService
        try:
            async for chunk in stream:
                sse_chunk = f'data: {json.dumps(chunk)}\n\n'
                debug_logger.debug(repr(sse_chunk))
                val = yield sse_chunk
                if val:
                    debug_logger.debug(val)
        finally:
            debug_logger.debug('send final message')
            yield 'event: done\ndata:{}\n\n'

    async def stop_generation(self, stream_id: uuid.UUID) -> None:
        if stream_id not in self._stream_pool:
            raise ValueError("Stream not found")

        stream = self._stream_pool[stream_id]
        assert stream.generator

        import asyncio
        from contextlib import suppress
        task = asyncio.create_task(stream.generator.__anext__())
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task
        await stream.generator.aclose()

        # await stream.generator.asend(StopAsyncIteration)
        del self._stream_pool[stream_id]

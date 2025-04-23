import json
import logging
import uuid
from pathlib import Path
from typing import Annotated, AsyncGenerator, ClassVar, Generator

from fastapi import Depends

from ..assistant.assistant_pool import AssistantPool
from ..assistant.chat_model import ChatAssistant
from ..logging.logging_config import setup_logging
from ..models.message import MessageDTO, ResponseChunkDTO
from ..repository.message import AsyncMessageRepository
from ..streaming import AsyncResponseGenerator, Stream

setup_logging()
debug_logger = logging.getLogger("debug")
logger = logging.getLogger('app')


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

    async def create_stream(
        self, chat_id: int, stream_id: uuid.UUID
    ) -> AsyncGenerator[str]:
        if stream_id not in self._stream_pool:
            raise ValueError("Stream not found")

        stream = self._stream_pool[stream_id]
        stream.generator = self._stream_message_mock()
        stream.is_running = True

        # TODO: need to abstract the SSE message format from the MessageService
        try:
            content_list = []
            chunk: ResponseChunkDTO
            async for chunk in stream:
                sse_chunk = f"data: {json.dumps(chunk)}\n\n"
                content_list.append(chunk["content"])

                debug_logger.debug(repr(sse_chunk))

                _ = yield sse_chunk
                
                if not stream.is_running:
                    break
                
            yield "event: done\ndata:{}\n\n"
        finally:
            logger.info("send final message")
            yield "event: done\ndata:{}\n\n"

            content = "".join(content_list)
            assistant_message = MessageDTO(content=content, role="assistant")
            await self._message_repository.create(chat_id, assistant_message)

    # FIXME: stop generation doesn't work
    async def stop_generation(self, stream_id: uuid.UUID) -> None:
        if stream_id not in self._stream_pool:
            raise ValueError("Stream not found")

        stream = self._stream_pool[stream_id]
        assert stream.generator

        stream.is_running = False

        # import asyncio
        # from contextlib import suppress

        # task = asyncio.create_task(stream.generator.__anext__())
        # task.cancel()
        # with suppress(asyncio.CancelledError):
        #     await task
        # await stream.generator.aclose()

        # await stream.generator.asend(StopAsyncIteration)
        del self._stream_pool[stream_id]

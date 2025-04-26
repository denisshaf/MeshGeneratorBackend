import json
import logging
import uuid
from pathlib import Path
from typing import Annotated, AsyncGenerator, ClassVar

from fastapi import Depends

from ..assistant.assistant_runner import AsyncProcessAssistantRunner
from ..assistant.chat_assistant import ChatAssistant, MockChatAssistant, ObjChatAssistant
# from ..assistant.llama import LlamaMock as Llama
from ..logging.logging_config import setup_logging
from ..models.message import MessageDTO, ResponseChunkDTO
from ..repository.message import AsyncMessageRepository
from ..streaming import AsyncResponseGenerator, Stream
from ..utils.object_pool import (
    AsyncObjectPool, AsyncPooledObjectContextManager
)
from ..utils.parser import OBJParser

from llama_cpp import Llama


setup_logging()
debug_logger = logging.getLogger("debug")
logger = logging.getLogger("app")


class MessageService:
    _stream_pool: ClassVar[dict[uuid.UUID, Stream]] = dict()
    _runner: ClassVar[AsyncProcessAssistantRunner] = AsyncProcessAssistantRunner()

    def __init__(
        self, message_repository: Annotated[AsyncMessageRepository, Depends()]
    ):
        self._message_repository = message_repository
        self._obj_parser = OBJParser()

    async def get_by_chat_id(self, chat_id: int) -> list[MessageDTO]:
        messages = await self._message_repository.get_by_chat_id(chat_id)
        return messages

    async def create_message(
        self, chat_id: int, message: MessageDTO
    ) -> tuple[uuid.UUID, MessageDTO]:
        debug_logger.debug(f"stream pool id: {id(self._stream_pool)}")
        message = await self._message_repository.create(chat_id, message)

        assert message.id

        stream_id = uuid.uuid4()
        self._stream_pool[stream_id] = Stream(chat_id, message.id)

        return stream_id, message

    @staticmethod
    def chat_assistant_factory() -> ChatAssistant:
        model_path = Path("~/LLaMA-Mesh/LLaMA-Mesh.gguf").expanduser()
        llm = Llama(
            model_path=str(model_path),
            n_ctx=4096,
            n_threads=12,
            verbose=False,
        )

        # chat_assistant = MockChatAssistant(llm=llm)
        # chat_assistant = ChatAssistant(llm=llm)
        chat_assistant = ObjChatAssistant(llm=llm)
        return chat_assistant

    async def _stream_message(
        self,
        message_history: list[ResponseChunkDTO],
        stream_id: uuid.UUID,
    ) -> AsyncResponseGenerator:
        assistant_pool = AsyncObjectPool[ChatAssistant].get_pool(
            self.chat_assistant_factory
        )

        async with AsyncPooledObjectContextManager(assistant_pool) as chat_assistant:
            gen = self._runner.stream_response(
                chat_assistant, message_history, stream_id
            )

            async for chunk in gen:
                yield chunk

    async def create_stream(
        self, chat_id: int, stream_id: uuid.UUID
    ) -> AsyncGenerator[str]:
        if stream_id not in self._stream_pool:
            raise ValueError("Stream not found")

        message_history = [
            ResponseChunkDTO(role="user", content="Genenerate a 3d-model of a chair")
        ]
        stream = self._stream_pool[stream_id]
        stream.generator = self._stream_message(message_history, stream_id)
        stream.is_running = True

        # TODO: need to abstract the SSE message format from the MessageService
        with self._obj_parser:
            try:
                content_list = []
                chunk: ResponseChunkDTO
                async for chunk in stream:
                    content = chunk["content"]
                    if content == "EOS":
                        break

                    sse_chunk = f"data: {json.dumps(chunk)}\n\n"
                    content_list.append(content)

                    self._obj_parser.process_token(content)

                    # debug_logger.debug(repr(sse_chunk))

                    yield sse_chunk

                    if not stream.is_running:
                        debug_logger.debug("stream stopped")
                        self._runner.stop_stream(stream_id)
                        break
            finally:
                obj_indexes_list = self._obj_parser.get_obj_indexes()

                debug_logger.debug(f'OBJ indexes: {obj_indexes_list}')
                for obj_indexes in obj_indexes_list:
                    yield f"event: obj_content\ndata:{json.dumps(obj_indexes)}\n\n"

                debug_logger.debug('send final message')
                logger.info("send final message")
                yield "event: done\ndata:{}\n\n"

                content = "".join(content_list)
                assistant_message = MessageDTO(content=content, role="assistant")
                await self._message_repository.create(chat_id, assistant_message)

                del self._stream_pool[stream_id]

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

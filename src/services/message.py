import logging
import uuid
from contextlib import aclosing
from enum import StrEnum
from typing import Annotated, AsyncGenerator, ClassVar, cast, Literal
from datetime import datetime

from fastapi import Depends

from ..assistant.assistant_runner import AsyncProcessAssistantRunner
from ..assistant.chat_assistant import (
    ChatAssistant, LlamaChatAssistant, LlamaMockChatAssistant,
    MockChatAssistant, ObjChatAssistant
)
from ..assistant.object_pool import (
    AsyncObjectPool, AsyncPooledObjectContextManager
)
from .parser import OBJParser
from ..models.message import MessageDTO, ResponseChunkDTO, MessageRole
# from ..assistant.llama import LlamaMock as Llama
from ..my_logging.logging_config import setup_logging
from ..repository.message import AsyncMessageRepository
from ..repository.model import AsyncModelRepository, AsyncS3ModelRepository
from ..routers.sse_streamer import ServerSentEvent
from .streaming import AsyncResponseGenerator, Stream

setup_logging()
debug_logger = logging.getLogger("debug")
logger = logging.getLogger("app")

logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)


class Event(StrEnum):
    OBJ_CONTENT = "obj_content"
    DONE = "done"
    ERROR = "error"
    BUSY = "busy"


class MessageService:    
    _stream_pool: ClassVar[dict[uuid.UUID, Stream]] = dict()
    _runner: ClassVar[AsyncProcessAssistantRunner | None] = None
    _max_workers: ClassVar[int | None] = None
    _implementation: ClassVar[str | None] = None

    def __init__(
        self,
        message_repository: Annotated[AsyncMessageRepository, Depends()],
        model_repository: Annotated[
            AsyncModelRepository, Depends(AsyncS3ModelRepository)
        ],
    ) -> None:
        self._message_repository = message_repository
        self._model_repository = model_repository

    @staticmethod
    def set_max_workers(max_workers: int) -> None:
        MessageService._max_workers = max_workers
        MessageService._runner = AsyncProcessAssistantRunner(max_workers)
    
    @staticmethod
    def set_assistant_implementation(implementation: str) -> None:
        MessageService._implementation = implementation

    async def get_by_chat_id(self, chat_id: int) -> list[MessageDTO]:
        messages = await self._message_repository.get_by_chat_id(chat_id)
        return messages

    async def create_message(
        self, chat_id: int, message: MessageDTO
    ) -> tuple[uuid.UUID, MessageDTO]:
        debug_logger.debug(f"stream pool id: {id(MessageService._stream_pool)}")
        message = await self._message_repository.create(chat_id, message)

        assert message.id

        stream_id = uuid.uuid4()
        MessageService._stream_pool[stream_id] = Stream(chat_id, message.id)

        return stream_id, message

    @staticmethod
    def chat_assistant_factory() -> ChatAssistant:
        implementation = MessageService._implementation

        if implementation == "llama":
            return LlamaChatAssistant()
        elif implementation == "mock":
            return MockChatAssistant()
        elif implementation == "llama_mock":
            return LlamaMockChatAssistant()
        elif implementation == "obj":
            return ObjChatAssistant()
        else:
            raise ValueError(f"Unknown assistant implementation: {implementation}")

    async def create_stream(
        self, chat_id: int, stream_id: uuid.UUID
    ) -> AsyncGenerator[ServerSentEvent]:
        debug_logger.debug(f"stream pool length: {len(MessageService._stream_pool)}")
        assert MessageService._runner
        assert MessageService._max_workers

        if stream_id not in MessageService._stream_pool:
            raise ValueError("Stream not found")

        messages = await self._message_repository.get_last_n_by_chat_id(chat_id, 1)
        message_history = [
            ResponseChunkDTO(role=cast(MessageRole, message.role), content=message.content)
            for message in messages
        ]

        assistant_pool = AsyncObjectPool.get_pool(
            MessageService.chat_assistant_factory,
            max_count=MessageService._max_workers
        )

        chat_assistant = await assistant_pool.acquire_nowait()

        if not chat_assistant:
            yield ServerSentEvent(event=Event.BUSY)
            
            chat_assistant = await assistant_pool.acquire()

        with OBJParser() as obj_parser:
            async with (
                aclosing(self._message_repository), 
                aclosing(self._model_repository)
            ):
                obj_indexes_list = []
                tokens = []
                chunk: ResponseChunkDTO
                try:

                    stream = MessageService._stream_pool[stream_id]
                    stream.generator = MessageService._runner.stream_response(
                        chat_assistant, message_history, stream_id
                    )
                    stream.is_running = True

                    async with aclosing(stream.generator) as stream_gen:
                        async for chunk in stream_gen:
                            if not stream.is_running:
                                MessageService._runner.stop_stream(stream_id)
                                break

                            content = chunk["content"]
                            if content == "EOS":
                                break

                            tokens.append(content)
                            obj_parser.process_token(content)
                            yield ServerSentEvent(data=chunk)

                    obj_indexes_list = obj_parser.get_obj_indexes()
                    parsed_content = OBJParser.extract_obj_content(
                        tokens, obj_indexes_list
                    )
                    message_content = parsed_content["message_content"]
                    obj_contents = parsed_content["obj_contents"]

                    content = "".join(tokens)
                    assistant_message = MessageDTO(
                        content=message_content, role="assistant"
                    )
                    created_message = await self._message_repository.create(
                        chat_id, assistant_message
                    )

                    for obj_content in obj_contents:
                        await self._model_repository.save(
                            cast(int, created_message.id), obj_content
                        )

                except Exception as e:
                    logger.error(f"Error during message generation: {e}")
                    yield ServerSentEvent(event=Event.ERROR, data=str(e))
                else:
                    yield ServerSentEvent(
                        event=Event.OBJ_CONTENT, data=obj_indexes_list
                    )
                    yield ServerSentEvent(event=Event.DONE)
                finally:
                    await assistant_pool.release(chat_assistant)
                    del MessageService._stream_pool[stream_id]

    @staticmethod
    async def stop_generation(stream_id: uuid.UUID) -> None:
        debug_logger.debug('stop_generation')
        if stream_id not in MessageService._stream_pool:
            raise ValueError("Stream not found")

        stream = MessageService._stream_pool[stream_id]
        assert stream.generator

        stream.is_running = False
    
    @staticmethod
    def shutdown() -> None:
        assert MessageService._runner
        MessageService._runner.shutdown()
        debug_logger.debug('stop_generation')

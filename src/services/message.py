import logging
import uuid
from contextlib import aclosing
from enum import StrEnum
from typing import Annotated, AsyncGenerator, ClassVar, cast

import yaml
from fastapi import Depends

from ..assistant.assistant_runner import AsyncProcessAssistantRunner
from ..assistant.chat_assistant import (
    ChatAssistant, LlamaChatAssistant, LlamaMockChatAssistant,
    MockChatAssistant, ObjChatAssistant
)
from ..assistant.object_pool import (
    AsyncObjectPool, AsyncPooledObjectContextManager
)
from ..assistant.parser import OBJParser
from ..db import SessionDependency
from ..models.message import MessageDTO, ResponseChunkDTO
# from ..assistant.llama import LlamaMock as Llama
from ..my_logging.logging_config import setup_logging
from ..repository.message import AsyncMessageRepository
from ..repository.model import AsyncModelRepository, AsyncS3ModelRepository
from ..routers.sse_streamer import ServerSentEvent
from ..streaming import AsyncResponseGenerator, Stream

setup_logging()
debug_logger = logging.getLogger("debug")
logger = logging.getLogger("app")

logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)


class Event(StrEnum):
    OBJ_CONTENT = "obj_content"
    DONE = "done"
    ERROR = "error"


class MessageService:
    _stream_pool: ClassVar[dict[uuid.UUID, Stream]] = dict()
    _runner: ClassVar[AsyncProcessAssistantRunner] = AsyncProcessAssistantRunner()

    def __init__(
        self,
        message_repository: Annotated[AsyncMessageRepository, Depends()],
        model_repository: Annotated[
            AsyncModelRepository, Depends(AsyncS3ModelRepository)
        ],
    ) -> None:
        self._message_repository = message_repository
        self._model_repository = model_repository
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
        with open("src/config.yaml") as file:
            config = yaml.safe_load(file)
            implementation = config["assistant"]["implementation"]

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

    async def _stream_message(
        self,
        message_history: list[ResponseChunkDTO],
        stream_id: uuid.UUID,
    ) -> AsyncResponseGenerator:
        assistant_pool = AsyncObjectPool[ChatAssistant].get_pool(
            MessageService.chat_assistant_factory
        )

        async with AsyncPooledObjectContextManager(assistant_pool) as chat_assistant:

            debug_logger.debug(f"chat_assistant: {chat_assistant}")

            gen = self._runner.stream_response(
                chat_assistant, message_history, stream_id
            )

            async for chunk in gen:
                yield chunk

    async def _mock_stream_message(
        self,
        message_history: list[ResponseChunkDTO],
        stream_id: uuid.UUID,
    ) -> AsyncResponseGenerator:
        import asyncio

        for i in range(10):
            yield ResponseChunkDTO(role="assistant", content=f"{i} ")
            await asyncio.sleep(1)

    async def create_stream(
        self, chat_id: int, stream_id: uuid.UUID
    ) -> AsyncGenerator[ServerSentEvent]:
        if stream_id not in self._stream_pool:
            raise ValueError("Stream not found")

        message_history = [
            ResponseChunkDTO(role="user", content="Genenerate a 3d-model of a chair")
        ]
        stream = self._stream_pool[stream_id]
        stream.generator = self._stream_message(message_history, stream_id)
        stream.is_running = True

        with self._obj_parser as obj_parser:
            async with aclosing(self._message_repository), aclosing(
                self._model_repository
            ):
                obj_indexes_list = []
                try:
                    tokens = []
                    chunk: ResponseChunkDTO

                    async with aclosing(stream.generator) as stream_gen:
                        async for chunk in stream_gen:
                            if not stream.is_running:
                                self._runner.stop_stream(stream_id)
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
                finally:
                    del self._stream_pool[stream_id]
                    yield ServerSentEvent(
                        event=Event.OBJ_CONTENT, data=obj_indexes_list
                    )
                    yield ServerSentEvent(event=Event.DONE)

    async def stop_generation(self, stream_id: uuid.UUID) -> None:
        if stream_id not in self._stream_pool:
            raise ValueError("Stream not found")

        stream = self._stream_pool[stream_id]
        assert stream.generator

        stream.is_running = False

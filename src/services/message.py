from pathlib import Path
from typing import AsyncGenerator, Generator

from ..assistant.assistant_pool import AssistantPool
from ..assistant.chat_model import ChatAssistant
from ..dependencies import get_db_session
from ..models.message import MessageDTO, ResponseChunkDTO
from ..repository.message import MessageRepository
from ..repository.repository import IAsyncRepository


class MessageService:
    def __init__(self, repository: IAsyncRepository):
        self._repository = repository
        self._stream_pool: dict[int, Generator] = dict()

    async def get_messages(self) -> list[MessageDTO]:
        messages = await self._repository.get()
        return messages

    async def create_message(self) -> MessageDTO:
        message = await self._repository.create()
        # chat_assistant.add_user_message(user_message)
        return message

    async def _stream_message(self) -> Generator:
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
                response_chunk = ResponseChunkDTO(role, content)
                yield response_chunk
        finally:
            assistant_pool.release(chat_assistant)

        answer = "".join(answer_list)
        message = MessageDTO()
        await self._repository.add(message)
        # chat_assistant.add_assistant_message(answer)

    async def create_stream(self, stream_id) -> Generator:
        stream = self._stream_message()
        self._stream_pool[stream_id] = stream

        # yield from stream
        async for chunk in stream:
            yield chunk

    def stop_generation(self, stream_id: int):
        stream = self._stream_pool[stream_id]
        stream.throw(Exception)


db_session = get_db_session()
user_repository = MessageRepository(db_session)
message_service = MessageService(user_repository)


def get_message_service() -> MessageService:
    return message_service

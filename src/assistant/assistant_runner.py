import asyncio
import functools
import multiprocessing as mp
import uuid
from concurrent.futures import ProcessPoolExecutor
from multiprocessing.synchronize import Event as EventClass
from queue import Empty, Queue
from typing import AsyncGenerator, ClassVar
import logging

from ..models.message import ResponseChunkDTO
from ..utils.singletone import Singleton
from .chat_assistant import ChatAssistant


debug_logger = logging.getLogger('debug')


class AsyncProcessAssistantRunner(metaclass=Singleton):
    _manager: ClassVar = mp.Manager()
    _process_pool: ClassVar = ProcessPoolExecutor(max_workers=4)
    _running_tasks: ClassVar[dict[uuid.UUID, asyncio.Future]] = {}
    _stop_events: ClassVar[dict[uuid.UUID, EventClass]] = {}

    def run_assistant(
        self,
        assistant: ChatAssistant,
        query: list[ResponseChunkDTO],
        queue: Queue,
        stop_event: EventClass,
    ) -> None:
        try:
            gen = assistant.generate_response(query)

            for chunk in gen:
                if stop_event.is_set():
                    break

                queue.put(chunk)
        except Exception as e:
            queue.put(e)
        finally:
            queue.put(None)

    async def _stream_from_queue(
        self,
        queue: Queue,
        stream_id: uuid.UUID,
    ) -> AsyncGenerator[ResponseChunkDTO, None]:
        loop = asyncio.get_event_loop()

        while True:
            try:
                chunk: ResponseChunkDTO | Exception | None = await loop.run_in_executor(
                    None, lambda: queue.get(block=True, timeout=60)  # 60 seconds
                )

                if not chunk:
                    break

                if isinstance(chunk, Exception):
                    raise chunk

                yield chunk
            except Empty:
                if (
                    stream_id in self._stop_events
                    and self._stop_events[stream_id].is_set()
                ):
                    break

                raise TimeoutError("Queue get timed out")

    def stream_response(
        self,
        assistant: ChatAssistant,
        query: list[ResponseChunkDTO],
        stream_id: uuid.UUID,
    ) -> AsyncGenerator[ResponseChunkDTO, None]:
        result_queue = self._manager.Queue()
        stop_event = self._manager.Event()
        self._stop_events[stream_id] = stop_event

        debug_logger.debug(f'assistant: {assistant}')

        loop = asyncio.get_running_loop()
        task = loop.run_in_executor(
            self._process_pool,
            functools.partial(
                self.run_assistant,
                assistant=assistant,
                query=query,
                queue=result_queue,
                stop_event=stop_event,
            ),
        )
        self._running_tasks[stream_id] = task

        return self._stream_from_queue(result_queue, stream_id)

    def stop_stream(self, stream_id: uuid.UUID) -> None:
        if stream_id in self._stop_events:
            self._stop_events[stream_id].set()

            if stream_id in self._running_tasks:
                self._running_tasks[stream_id].cancel()
                del self._running_tasks[stream_id]

            del self._stop_events[stream_id]

    def shutdown(self) -> None:
        for stop_event in self._stop_events.values():
            stop_event.set()

        for task in self._running_tasks.values():
            task.cancel()

        self._running_tasks.clear()
        self._stop_events.clear()

        self._process_pool.shutdown(wait=False)
        self._manager.shutdown()

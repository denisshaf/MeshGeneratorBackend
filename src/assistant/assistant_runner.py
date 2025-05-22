import os
import asyncio
import functools
import logging
import multiprocessing as mp
import uuid
from concurrent.futures import ProcessPoolExecutor
from multiprocessing.synchronize import Event as EventClass
from queue import Empty, Queue
from typing import AsyncGenerator, ClassVar

from ..models.message import ResponseChunkDTO
from .chat_assistant import ChatAssistant

debug_logger = logging.getLogger("debug")


class AsyncProcessAssistantRunner:
    MAX_WORKERS_DEFAULT = 1

    # _manager = mp.Manager()
    # _process_pool = ProcessPoolExecutor(3)
    # _running_tasks: dict[uuid.UUID, asyncio.Future] = {}
    # _stop_events: dict[uuid.UUID, EventClass] = {}

    def __init__(self, max_workers: int = MAX_WORKERS_DEFAULT):
        self._manager = mp.Manager()
        self._process_pool = ProcessPoolExecutor(max_workers)
        self._running_tasks: dict[uuid.UUID, asyncio.Future] = {}
        self._stop_events: dict[uuid.UUID, EventClass] = {}
        ...

    # def __getstate__(self):
    #     d = super().__getstate__()
    #     d_copy = dict(d)

    #     del d_copy['_manager']
    #     del d_copy['_process_pool']
    #     del d_copy['_running_tasks']
    #     del d_copy['_stop_events']

    #     return d_copy

    @staticmethod
    def _run_assistant(
        assistant: ChatAssistant,
        query: list[ResponseChunkDTO],
        queue: Queue,
        stop_event: EventClass,
    ) -> None:
        try:
            debug_logger.debug(f"Run in process {os.getpid()}, {queue=}")
            print(f"Run in process {os.getpid()}, {queue=}", flush=True)
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

                raise TimeoutError("Queue got timed out")

    def stream_response(
        self,
        assistant: ChatAssistant,
        query: list[ResponseChunkDTO],
        stream_id: uuid.UUID,
    ) -> AsyncGenerator[ResponseChunkDTO, None]:
        debug_logger.debug(f"_process_pool: {self._process_pool=}")

        result_queue = self._manager.Queue()

        debug_logger.debug(f"stream_response: {stream_id=}, queue={result_queue}")
        stop_event = self._manager.Event()
        self._stop_events[stream_id] = stop_event

        loop = asyncio.get_running_loop()
        task = loop.run_in_executor(
            self._process_pool,
            functools.partial(
                AsyncProcessAssistantRunner._run_assistant,
                assistant=assistant,
                query=query,
                queue=result_queue,
                stop_event=stop_event,
            ),
        )
        debug_logger.debug(f"task: {task}")
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

from __future__ import annotations

import asyncio
import logging
from types import TracebackType
from typing import Callable, ClassVar

from ..logging.logging_config import setup_logging

setup_logging()
debug_logger = logging.getLogger("debug")


class AsyncObjectPool[T]:
    _queue: asyncio.Queue[T] = asyncio.Queue()
    _lock = asyncio.Lock()
    _created_count = 0
    _pool: ClassVar[AsyncObjectPool[T] | None] = None

    @classmethod
    def get_pool(
        cls: type[AsyncObjectPool[T]], factory: Callable[[], T], max_count: int = 3
    ) -> AsyncObjectPool[T]:
        debug_logger.debug(f"get_pool: class = {cls}, {cls._pool=}")
        if not cls._pool:
            pool = cls(factory, max_count)
            cls._pool = pool
        else:
            pool = cls._pool
        return pool

    def __init__(self, factory: Callable[[], T], max_count: int) -> None:
        self._max_count = max_count
        self._factory = factory

    async def acquire(self, timeout: float | None = None) -> T:
        debug_logger.debug(f"acquire from pool {self}")
        debug_logger.debug(f"created objects: {self._created_count}")

        try:
            obj = self._queue.get_nowait()
            debug_logger.debug("Objects are free. Get the object")
            return obj
        except asyncio.QueueEmpty:
            async with self._lock:
                if self._created_count < self._max_count:
                    self._created_count += 1
                    debug_logger.debug(
                        f"Object created. Objects: {self._created_count}"
                    )

                    loop = asyncio.get_event_loop()
                    obj = await loop.run_in_executor(None, self._factory)
                    return obj

        debug_logger.debug("Wait to get an object")
        if timeout:
            try:
                obj = await asyncio.wait_for(self._queue.get(), timeout)
                debug_logger.debug("Object acquired after waiting")
                return obj
            except asyncio.TimeoutError:
                debug_logger.debug("Timeout waiting for object")
                raise TimeoutError(
                    f"Timed out waiting for object after {timeout} seconds"
                )
        else:
            obj = await self._queue.get()
            debug_logger.debug("Object acquired after waiting")
            return obj

    async def release(self, obj: T) -> None:
        await self._queue.put(obj)
        debug_logger.debug(f"Object released. Queue size: {self._queue.qsize()}")


class AsyncPooledObjectContextManager[T]:
    _obj: T | None = None

    def __init__(self, pool: AsyncObjectPool[T], timeout: float | None = None) -> None:
        self.pool = pool
        self.timeout = timeout

    async def __aenter__(self) -> T:
        self._obj = await self.pool.acquire(self.timeout)
        return self._obj

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if not self._obj:
            raise TypeError("__aenter__ was not called")
        await self.pool.release(self._obj)


class ObjectPool[T]:
    _pool: ClassVar[ObjectPool[T] | None] = None
    _async_pool: AsyncObjectPool[T]

    @classmethod
    def get_pool(
        cls: type[ObjectPool[T]], factory: Callable[[], T], max_count: int = 1
    ) -> ObjectPool[T]:
        debug_logger.debug(f"get_pool: class = {cls}, {cls._pool=}")
        if not cls._pool:
            pool = cls(factory, max_count)
            cls._pool = pool
        else:
            pool = cls._pool
        return pool

    def __init__(self, factory: Callable[[], T], max_count: int = 1):
        self._async_pool = AsyncObjectPool(factory, max_count)

    def acquire(self, timeout: float | None = None) -> T:
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(self._async_pool.acquire(timeout))
        finally:
            loop.close()

    def release(self, obj: T) -> None:
        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(self._async_pool.release(obj))
        finally:
            loop.close()


class PooledObjectContextManager[T]:
    _obj: T | None = None

    def __init__(self, pool: ObjectPool[T], timeout: float | None = None) -> None:
        self.pool = pool
        self.timeout = timeout

    def __enter__(self) -> T:
        self._obj = self.pool.acquire(self.timeout)
        return self._obj

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if not self._obj:
            raise TypeError("__enter__ was not called")
        self.pool.release(self._obj)

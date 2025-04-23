from __future__ import annotations

from abc import ABC, abstractmethod
from typing import ClassVar


class AbstractPool[T](ABC):
    _max_count: int
    _instances: list[T]
    _pool: ClassVar[AbstractPool | None] = None

    @classmethod
    def get_pool(cls: type[AbstractPool]) -> AbstractPool:
        pool = cls._pool if cls._pool else cls()
        return pool

    def __init__(self, max_count: int = 1):
        self._max_count = max_count
        self._instances = []

    @abstractmethod
    def get_instance(self) -> T: ...

    @abstractmethod
    def release(self, instance: T) -> None: ...

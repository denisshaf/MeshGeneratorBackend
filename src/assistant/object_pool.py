from __future__ import annotations

from abc import ABC, abstractmethod
from typing import ClassVar


class AbstractPool:
    _pool: ClassVar[AbstractPool | None] = None

    @classmethod
    def get_pool(cls):
        pool = cls._pool if cls._pool else cls()
        return pool

    def __init__(self, max_count: int):
        self._max_count = max_count
        self._instances = []

    @abstractmethod
    def get_instance(): ...

    @abstractmethod
    def release(instance): ...

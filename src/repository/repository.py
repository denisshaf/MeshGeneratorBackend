from abc import ABC, abstractmethod
from typing import Generic, TypeVar

T = TypeVar("T")


class IAsyncRepository(Generic[T], ABC):
    @abstractmethod
    async def create(self, dto: T) -> T: ...

    @abstractmethod
    async def get(self, id: str) -> T | None: ...

    @abstractmethod
    async def update(self, dto: T) -> T | None: ...

    @abstractmethod
    async def delete(self, id: str) -> bool: ...

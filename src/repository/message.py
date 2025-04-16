from ..models.message import MessageDTO
from .repository import IAsyncRepository


class MessageRepository(IAsyncRepository):
    def __init__(self, db_session):
        self.db_session = db_session

    async def create(self, message: MessageDTO) -> MessageDTO: ...

    async def get(self, auth_id: str) -> MessageDTO: ...

    async def update(self, message: MessageDTO) -> MessageDTO: ...

    async def delete(self, auth_id: str) -> bool: ...

from __future__ import annotations

from datetime import datetime
from typing import TypedDict, Optional
import typing

from pydantic import BaseModel, ConfigDict
from sqlalchemy import ForeignKey, Index, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import Base
if typing.TYPE_CHECKING:
    from .chat_role import ChatRoleDAO
    from .chat import ChatDAO
    from .model import ModelDAO


class MessageDAO(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    chat_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("chats.id", ondelete="CASCADE", onupdate="CASCADE")
    )
    role_id: Mapped[int] = mapped_column(ForeignKey("chat_roles.id"))

    chat: Mapped[Optional['ChatDAO']] = relationship(back_populates="messages")
    role: Mapped['ChatRoleDAO'] = relationship(back_populates="messages")
    models: Mapped[list['ModelDAO']] = relationship(
        back_populates="message", cascade="all, delete-orphan"
    )

    __table_args__ = (Index("messages_chat_id_idx", "chat_id"),)

    def __repr__(self) -> str:
        return (
            f"<Message(id={self.id}, chat_id={self.chat_id}, role_id={self.role_id})>"
        )


class MessageDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
    content: str
    role: str | None = None
    created_at: datetime | None = None
    chat_id: int | None = None


class ResponseChunkDTO(TypedDict):
    role: str
    content: str

from __future__ import annotations

import typing
from datetime import datetime

from pydantic import BaseModel, ConfigDict
from sqlalchemy import ForeignKey, Index, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import Base

if typing.TYPE_CHECKING:
    from .message import MessageDAO
    from .user import UserDAO


class ChatDAO(Base):
    __tablename__ = "chats"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(Text, default="Chat")
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE", onupdate="CASCADE")
    )

    user: Mapped["UserDAO"] = relationship(back_populates="chats")
    messages: Mapped[list["MessageDAO"]] = relationship(
        back_populates="chat", cascade="all, delete-orphan"
    )

    __table_args__ = (Index("chats_user_id_idx", "user_id"),)

    def __repr__(self) -> str:
        return f"<Chat(id={self.id}, title='{self.title}', user_id={self.user_id})>"


class ChatDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
    title: str
    user_id: int | None = None
    created_at: datetime

from __future__ import annotations
import typing

from pydantic import BaseModel, ConfigDict
from sqlalchemy import SmallInteger, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import Base
if typing.TYPE_CHECKING:
    from .message import MessageDAO


class ChatRoleDAO(Base):
    __tablename__ = "chat_roles"

    id: Mapped[int] = mapped_column(SmallInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(Text, unique=True)

    messages: Mapped[list['MessageDAO']] = relationship(back_populates="role")

    def __repr__(self) -> str:
        return f"<ChatRole(id={self.id}, name='{self.name}')>"


class ChatRoleDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str

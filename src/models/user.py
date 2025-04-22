from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import DateTime, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import Base
from .chat import ChatDAO
from .model import ModelDAO


class UserDAO(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(Text, server_default="User")
    auth_id: Mapped[str] = mapped_column(Text, unique=True)
    email: Mapped[Optional[str]] = mapped_column(Text, unique=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    chats: Mapped[list["ChatDAO"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    models: Mapped[list["ModelDAO"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, name='{self.name}', auth_id='{self.auth_id}', email='{self.email}'), created_at='{self.created_at}')>"


class UserDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
    name: str
    auth_id: str = Field(serialization_alias="sub")
    email: str
    created_at: datetime | None = None

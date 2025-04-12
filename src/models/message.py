from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Integer,
    Text,
    ForeignKey
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship
)
from . import Base


class Message(Base):
    __tablename__ = 'messages'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime]

    chat_id: Mapped[Optional[int]] = mapped_column(ForeignKey('chats.id'))
    role_id: Mapped[int] = mapped_column(ForeignKey('roles.id'))
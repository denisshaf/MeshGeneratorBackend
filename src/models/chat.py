from datetime import datetime
from sqlalchemy import (
    Integer,
    Text,
    DateTime,
    ForeignKey
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship
)
from . import Base


class Chat(Base):
    __tablename__ = 'chats'

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime]

    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column
)
from . import Base


class Model(Base):
    __tablename__ = 'models'

    id: Mapped[int] = mapped_column(primary_key=True)
    filename: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime]
    content: Mapped[Optional[str]] = mapped_column(Text)
    storage_path: Mapped[Optional[str]] = mapped_column(String(2048))

    message_id: Mapped[Optional[int]] = mapped_column(ForeignKey('messages.id'))
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey('users.id'))
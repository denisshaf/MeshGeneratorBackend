from typing import Optional
from datetime import datetime
from sqlalchemy import Integer, Text, DateTime
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship
)
from . import Base


class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primaty_key=True)
    name: Mapped[str] = mapped_column(Text)
    auth_id: Mapped[str] = mapped_column(Text, unique=True)
    email: Mapped[Optional[str]] = mapped_column(Text, unique=True)
    created_at: Mapped[datetime]

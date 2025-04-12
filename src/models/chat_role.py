from sqlalchemy import (
    SmallInteger,
    Text
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship
)
from . import Base


class ChatRole(Base):
    __tablename__ = 'roles'

    id: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    name: Mapped[str] = mapped_column(Text, unique=True)
from __future__ import annotations

import typing
from datetime import datetime
from typing import Optional, Any, Self, Annotated

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import ForeignKey, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import Base

if typing.TYPE_CHECKING:
    from .message import MessageDAO
    from .user import UserDAO


class ModelDAO(Base):
    __tablename__ = "models"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), server_default="3DModel")
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    content: Mapped[Optional[str]] = mapped_column(Text)
    storage_path: Mapped[Optional[str]] = mapped_column(String(2048))

    message_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("messages.id", ondelete="SET NULL", onupdate="CASCADE")
    )
    user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE", onupdate="CASCADE")
    )

    message: Mapped[Optional["MessageDAO"]] = relationship(back_populates="models")
    user: Mapped[Optional["UserDAO"]] = relationship(back_populates="models")

    __table_args__ = (Index("models_user_id_idx", "user_id"),)

    def __repr__(self) -> str:
        return f"<Model(id={self.id}, filename='{self.name}', user_id={self.user_id})>"


class ModelDTO(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        validate_by_name=True,
        validate_by_alias=True
    )

    id: int | None
    name: str
    content: str | None = None
    url: Annotated[str | None, Field(validation_alias="storage_path")] = None
    created_at: datetime | None = None
    is_saved: bool = False

    @classmethod
    def model_validate(
        cls,
        obj: Any,
        *,
        strict: bool | None = None,
        from_attributes: bool | None = None,
        context: Any = None,
        by_alias: bool | None = None,
        by_name: bool | None = None
    ) -> Self:
        result = super().model_validate(
            obj,
            strict=strict,
            from_attributes=from_attributes,
            context=context,
            by_alias=by_alias,
            by_name=by_name
        )

        if isinstance(obj, Base) and hasattr(obj, "user_id"):
            result.is_saved = obj.user_id is not None
        
        return result


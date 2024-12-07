from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import UUID, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base


class ActiveSession(Base):
    __tablename__ = "active_session"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE")
    )
    refresh_token_hash: Mapped[str]
    issued_at: Mapped[datetime]
    expires_at: Mapped[datetime]
    device_info: Mapped[str]

    user: Mapped[user.User] = relationship(back_populates="active_session")


class SessionHistory(Base):
    __tablename__ = "session_history"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("user.id", ondelete="SET NULL")
    )
    refresh_token_hash: Mapped[str | None]
    issued_at: Mapped[datetime | None]
    expires_at: Mapped[datetime | None]
    device_info: Mapped[str]
    # Подход объединения логики с access и refresh токенами в одной таблице
    # истории не очень красиво выглядит, т.к. если access токен,
    # то колонки связанные с refresh будут пустыми, и наоборот.
    # Но как сделать лучше - в голову не пришло
    jti: Mapped[str | None]
    last_login: Mapped[datetime | None]

    user: Mapped[user.User | None] = relationship(
        back_populates="session_history"
    )

from __future__ import annotations

import uuid
from datetime import datetime
from typing import List

from sqlalchemy import UUID, Column, DateTime, ForeignKey, String, Table, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models import session
from models.base import Base

user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", ForeignKey("user.id"), primary_key=True),
    Column("role_id", ForeignKey("role.id"), primary_key=True),
)


class User(Base):
    """
    Таблица пользователей.

    Поля:
    - id: Уникальный идентификатор пользователя (UUID).
    - created_at: Дата и время создания записи.
    - login: Уникальный логин пользователя.
    - password_hash: Хэш пароля пользователя.
    - first_name: Имя пользователя (опционально).
    - last_name: Фамилия пользователя (опционально).

    Отношения:
    - roles: Связь M2M через промежуточную таблицу
        `user_roles` с таблицей ролей.
    - active_session: Связь с таблицей `active_session`.
    - session_history: Связь с таблицей `session_history`.
    """

    __tablename__ = "user"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    login: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    first_name: Mapped[str] = mapped_column(String(255), default="")
    last_name: Mapped[str] = mapped_column(String(255), default="")

    roles: Mapped[List[Role]] = relationship(secondary=user_roles)
    active_session: Mapped[List[session.ActiveSession]] = relationship(
        back_populates="user"
    )
    session_history: Mapped[List[session.SessionHistory]] = relationship(
        back_populates="user"
    )


class Role(Base):
    """
    Таблица ролей пользователей.

    Поля:
    - id: Уникальный идентификатор роли (UUID).
    - name: Уникальное название роли.
    - description: Описание роли (опционально).

    Отношения:
    - users: Связь M2M через промежуточную таблицу
        `user_roles` с таблицей пользователей.
    """

    __tablename__ = "role"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    description: Mapped[str] = mapped_column(String, default="")

    users: Mapped[List[User]] = relationship(secondary=user_roles)

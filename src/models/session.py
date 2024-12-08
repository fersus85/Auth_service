from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import UUID, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base


class ActiveSession(Base):
    """
    Таблица активных сессий пользователей.

    Поля:
    - id: Уникальный идентификатор сессии (UUID).
    - user_id: Идентификатор пользователя (ForeignKey на таблицу user).
    - refresh_token_hash: Хэш refresh-токена,
        используемого для обновления доступа.
    - issued_at: Время выпуска refresh-токена.
    - expires_at: Время истечения refresh-токена.
    - device_info: Информация об устройстве, с которого инициирована сессия.

    Отношения:
    - user: Связь с таблицей user (обратное отношение через `active_session`).
    """

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


class SessionHistoryChoices(enum.Enum):
    LOGIN_WITH_PASSWORD = "Login with password"
    REFRESH_TOKEN_UPDATE = "Refreshable token updated"
    USER_LOGOUT = "User logout"


class SessionHistory(Base):
    """
    Таблица истории сессий пользователей.

    Поля:
    - id: Уникальный идентификатор записи истории сессии (UUID).
    - name (SessionHistoryChoices): Действие связанное с сессией.
        Возможные значения:
            - LOGIN_WITH_PASSWORD: Вход пользователя с использованием пароля.
            - REFRESH_TOKEN_UPDATE: Обновление refresh-токена.
            - USER_LOGOUT: Выход пользователя из системы.
    - user_id: Идентификатор пользователя (ForeignKey на таблицу user).
        Может быть NULL, если пользователь удалён.
    - refresh_token_hash: Хэш refresh-токена.
        Может быть NULL, если лог USER_LOGOUT
    - issued_at: Время выпуска refresh-токена.
        Может быть NULL, если лог USER_LOGOUT
    - expires_at: Время истечения refresh-токена.
        Может быть NULL, если лог USER_LOGOUT
    - device_info: Информация об устройстве, связанном с событием.
    - created_at: Дата и время создания записи.
        По умолчанию заполняется текущим временем на сервере.

    Отношения:
    - user: Связь с таблицей user (обратное отношение через `session_history`).
    """

    __tablename__ = "session_history"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[SessionHistoryChoices]
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("user.id", ondelete="SET NULL")
    )
    refresh_token_hash: Mapped[str] = mapped_column(String, default="")
    issued_at: Mapped[datetime]
    expires_at: Mapped[datetime]
    device_info: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    user: Mapped[user.User | None] = relationship(
        back_populates="session_history"
    )

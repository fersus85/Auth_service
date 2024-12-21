from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class UserBase(BaseModel):
    login: str
    first_name: str | None = None
    last_name: str | None = None

    model_config = ConfigDict(from_attributes=True)


class UserFull(UserBase):
    id: UUID
    created_at: datetime | None = None


class UserRole(UserFull):
    password_hash: str | None = None
    role: str | None = None


# Ниже User для CRUD
class UserCreate(UserBase):
    password: str


class UserRead(UserFull):
    pass


class UserUpdate(BaseModel):
    """
    Модель для частичного обновления данных пользователя.

    Поля, установленные в None, не изменяются.
    """

    first_name: str | None = None
    last_name: str | None = None
    password: str | None = None

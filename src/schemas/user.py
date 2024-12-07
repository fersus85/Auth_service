from datetime import datetime
from typing import List
from uuid import UUID

from pydantic import BaseModel

from src.schemas.role import RoleFull


class UserBase(BaseModel):
    login: str
    created_at: datetime
    first_name: str | None = None
    last_name: str | None = None


class UserFull(UserBase):
    id: UUID


class UserRole(UserFull):
    roles: List[RoleFull] | None = None


# Ниже User для CRUD
class UserCreate(UserRole):
    password: str


class UserRead(UserBase):
    pass


class UserUpdate(BaseModel):
    # Если атрибут is None, то менять не нужно.
    # Для разграничения None и пустого значения
    # можно использовать exclude_unset=True
    first_name: str | None = None
    last_name: str | None = None

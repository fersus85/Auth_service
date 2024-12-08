from uuid import UUID

from pydantic import BaseModel


class RoleBase(BaseModel):
    name: str
    description: str | None = None

    class Config:
        from_attributes = True


class RoleFull(RoleBase):
    id: UUID


# Ниже Role для CRUD
class RoleCreate(RoleBase):
    pass


class RoleRead(RoleFull):
    pass


class RoleUpdate(RoleBase):
    """
    Модель для частичного обновления данных ролей.

    Поля, установленные в None, не изменяются.
    """

    name: str | None = None

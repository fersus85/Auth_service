from uuid import UUID

from pydantic import BaseModel


class RoleBase(BaseModel):
    name: str
    description: str | None = None


class RoleFull(RoleBase):
    id: UUID


# Ниже Role для CRUD
class RoleCreate(RoleBase):
    pass


class RoleRead(RoleFull):
    pass


class RoleUpdate(RoleBase):
    # Если атрибут is None, то менять не нужно.
    # Для разграничения None и пустого значения
    # можно использовать exclude_unset=True
    name: str | None = None

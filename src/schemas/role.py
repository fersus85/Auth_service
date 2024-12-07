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
    # если атрибут is None, то менять не нужно
    name: str | None = None

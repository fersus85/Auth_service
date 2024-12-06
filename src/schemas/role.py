from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class RoleBase(BaseModel):
    name: str
    description: Optional[str] = None


class RoleFull(RoleBase):
    id: UUID


class RoleCreate(RoleBase):
    pass


class RoleRead(RoleFull):
    pass


class RoleUpdate(RoleBase):
    name: str | None = None

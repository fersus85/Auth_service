from typing import Set

from fastapi import Depends, HTTPException, status

from schemas.auth import AccessJWT
from services.role.role_service import RoleService, get_role_service
from services.utils import get_params_from_refresh_token


class PermissionChecker:
    def __init__(self, required: Set[str]) -> None:
        self.required = required

    def __call__(
        self,
        access: AccessJWT = Depends(get_params_from_refresh_token),
        role_service: RoleService = Depends(get_role_service),
    ) -> bool:
        if not any(True for role in access.roles if role in self.required):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )

        return True
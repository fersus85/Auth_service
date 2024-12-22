from typing import Set

from fastapi import Depends, HTTPException, status

from schemas.auth import AccessJWT
from services.role.role_service import RoleService, get_role_service
from services.utils import get_params_from_refresh_token


class PermissionChecker:
    """
    Класс для проверки прав доступа пользователя.

    Этот класс используется как зависимость в маршрутах FastAPI для проверки,
    имеет ли текущий пользователь хотя бы одну из требуемых ролей.
    Если у пользователя недостаточно прав,
    выбрасывается исключение HTTP 403 Forbidden.
    """

    def __init__(self, required: Set[str]) -> None:
        self.required = required

    def __call__(
        self,
        access: AccessJWT = Depends(get_params_from_refresh_token),
        role_service: RoleService = Depends(get_role_service),
    ) -> bool:
        """
        Проверяет, имеет ли пользователь хотя бы одну из требуемых ролей.
        """
        if access.role not in self.required:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions",
            )

        return True

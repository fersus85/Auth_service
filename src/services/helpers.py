import secrets
import string
from typing import Set

from fastapi import Depends, HTTPException, Response, status

from schemas.auth import AccessJWT, UserTokenResponse
from services.role.role_service import RoleService, get_role_service
from services.utils import get_params_from_refresh_token


def set_tokens_in_cookies(
    response: Response, tokens: UserTokenResponse
) -> None:
    """
    Устанавливет токены в cookies
    """
    response.set_cookie(
        key="access_token",
        value=tokens.access_token,
        httponly=True,
        samesite="lax",
    )
    response.set_cookie(
        key="refresh_token",
        value=tokens.refresh_token,
        httponly=True,
        samesite="lax",
    )


def generate_secure_password(length=12):
    """
    Генерирует безопасный пароль заданной длины.

    Параметры:
    length (int): Длина генерируемого пароля. По умолчанию 12.

    Возвращает:
    str: Сгенерированный пароль, состоящий из букв, цифр и спец символов.
    """
    characters = string.ascii_letters + string.digits + string.punctuation
    password = "".join(secrets.choice(characters) for _ in range(length))
    return password


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

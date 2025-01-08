import secrets
import string
from base64 import b64encode
from typing import Set

import requests
from fastapi import Depends, HTTPException, Response, status

from core.config import settings
from schemas.auth import AccessJWT, UserTokenResponse
from services.role.role_service import RoleService, get_role_service
from services.utils import get_params_from_refresh_token


async def yndx_info_request(resp_token: dict) -> dict:
    """
    Запрашивает информацию о пользователе из Yandex OAuth.

    Args:
        resp_token (dict): Словарь, содержащий токен доступа,
        полученный после авторизации.

    Returns:
        dict: Словарь с информацией о пользователе, полученной от Yandex.
    """
    headers = {
        "Authorization": f"OAuth {resp_token['access_token']}",
    }

    response_info = requests.get(
        url=settings.yndx_oauth.INFO_URL, headers=headers
    )
    return response_info.json()


async def yndx_token_request(code: str) -> dict:
    """
    Запрашивает токен доступа Yandex OAuth с использованием
    кода авторизации.

    Args:
        code (str): Код авторизации, полученный после успешной
        авторизации пользователя.

    Returns:
        dict: Словарь с токеном доступа и другой информацией,
        полученной от Yandex.
    """
    client_id = settings.yndx_oauth.CLIENT_ID
    client_secret = settings.yndx_oauth.CLIENT_SECRET
    raw_str = f"{client_id}:{client_secret}"
    encoded_creds = b64encode(raw_str.encode()).decode()

    data = {"grant_type": "authorization_code", "code": code}

    headers = {
        "Content-type": "application/x-www-form-urlencoded",
        "Authorization": f"Basic {encoded_creds}",
    }

    token_resp = requests.post(
        url=settings.yndx_oauth.TOKEN_URL, headers=headers, data=data
    )

    return token_resp.json()


async def vk_token_request(
    code: str, code_verifier: str, device_id: str, state: str
) -> dict:
    """
    Запрашивает токен доступа VK OAuth с использованием
    кода авторизации.

    Args:
        code (str): Код авторизации, полученный после успешной
        авторизации пользователя.
        code_verifier (str): сгенерированный на прошлом шаге код PKCE
        device_id (str): устройство пользователя, полученное от VK
        state (str): уникальная строка

    Returns:
        dict: Словарь с токеном доступа и другой информацией,
        полученной от VK.
    """
    client_id = settings.vk_oauth.CLIENT_ID
    client_secret = settings.vk_oauth.CLIENT_SECRET
    raw_str = f"{client_id}:{client_secret}"
    encoded_creds = b64encode(raw_str.encode()).decode()

    data = {
        "grant_type": "authorization_code",
        "code": code,
        "code_verifier": code_verifier,
        "client_id": client_id,
        "device_id": device_id,
        "state": state,
        "redirect_uri": "https://localhost/api/v1/oauth/vk_callback",
    }

    headers = {
        "Content-type": "application/x-www-form-urlencoded",
        "Authorization": f"Basic {encoded_creds}",
    }

    token_resp = requests.post(
        url=settings.vk_oauth.TOKEN_URL, headers=headers, data=data
    )

    return token_resp.json()


async def vk_info_request(resp_token: dict) -> dict:
    """
    Запрашивает информацию о пользователе из VK OAuth.

    Args:
        resp_token (dict): Словарь, содержащий токен доступа,
        полученный после авторизации.

    Returns:
        dict: Словарь с информацией о пользователе, полученной от VK.
    """

    headers = {
        "Content-type": "application/x-www-form-urlencoded",
    }

    data = {
        "access_token": resp_token["access_token"],
        "client_id": settings.vk_oauth.CLIENT_ID,
    }

    response_info = requests.post(
        url=settings.vk_oauth.INFO_URL, data=data, headers=headers
    )

    return response_info.json()


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


async def convert_vk_user_info_to_yndx(resp_info_dict: dict) -> dict:
    """
    Конвертирует User Info VK в формат Yandex User Info,
    чтобы далее использовать общие функции и не дублировать код
    """
    resp_info_dict: dict = resp_info_dict.get("user", None)

    resp_info_dict["display_name"] = resp_info_dict.get(
        "display_name",
        f"{resp_info_dict['first_name']} {resp_info_dict['last_name']}",
    )
    resp_info_dict["real_name"] = resp_info_dict.get(
        "real_name", resp_info_dict.get("display_name", "")
    )
    resp_info_dict["login"] = resp_info_dict.get(
        "login", resp_info_dict.get("email", "")
    )
    resp_info_dict["sex"] = str(resp_info_dict.get("sex", None))
    resp_info_dict["id"] = resp_info_dict.get("user_id", "")
    resp_info_dict["client_id"] = resp_info_dict.get("user_id", "")
    resp_info_dict["psuid"] = ""

    return resp_info_dict


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

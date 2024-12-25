import logging
from base64 import b64encode
from typing import Annotated
from urllib.parse import urlencode

import requests
from fastapi import (
    APIRouter,
    Body,
    Depends,
    Header,
    HTTPException,
    Query,
    Request,
    Response,
    status,
)
from pydantic import BaseModel

from core.config import settings
from responses.auth_responses import (
    get_change_psw_response,
    get_login_response,
    get_signup_response,
    get_token_refr_response,
)
from schemas.auth import UserLogin, UserLoginResponse, UserTokenResponse
from schemas.user import UserCreate, UserRead, UserUpdate
from schemas.yndx_oauth import UserInfoSchema
from services.auth.auth_service import AuthService, get_auth_service
from services.utils import (
    get_user_id_from_access_token,
    get_user_id_from_refresh_token,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/signup",
    status_code=status.HTTP_201_CREATED,
    response_model=UserRead,
    summary="User registration",
    description="User registration endpoint, requires username and password.",
    responses=get_signup_response(),
)
async def signup_user(
    user_create: UserCreate = Body(
        ...,
        description="login, password, first_name (опц), last_name(опц)",
    ),
    auth_service: AuthService = Depends(get_auth_service),
) -> UserRead:
    """
    Регистрация нового пользователя
    """
    logger.info("signup user %s", user_create.login)

    result = await auth_service.signup_user(user_create)

    return result


@router.post(
    "/login",
    status_code=status.HTTP_200_OK,
    response_model=UserLoginResponse,
    summary="User login",
    description="User login endpoint returns access and refresh tokens",
    responses=get_login_response(),
)
async def login_user(
    response: Response,
    user_login: UserLogin = Body(
        ...,
        description="login, password for sign in app",
    ),
    user_agent: Annotated[str | None, Header()] = None,
    auth_service: AuthService = Depends(get_auth_service),
) -> UserLoginResponse:
    """
    Аутентификация пользователя по логину и паролю.
    Выдача токенов.
    """
    logger.info("login attempt from user %s", user_login.login)

    user, tokens = await auth_service.login_user(user_login, user_agent)

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
    return user


@router.get(
    "/yndx_social_login",
    status_code=status.HTTP_200_OK,
    summary="OAuth 2.0 Yndx login",
    description="Redirects to Yandex OAuth 2.0 login page.",
)
async def yndx_social_login():
    params = {
        "response_type": "code",
        "client_id": settings.yndx_oauth.YNDX_CLIENT_ID,
    }
    auth_url = f"{settings.yndx_oauth.YNDX_CODE_URL}?{urlencode(params)}"
    logger.warning("url: %s", auth_url)
    return {"url_for_auth": auth_url}


@router.get(
    "/yndx_callback",
    response_model="",
    status_code=status.HTTP_200_OK,
    summary="OAuth 2.0 Yndx login",
    description="Redirects to Yandex OAuth 2.0 login page.",
)
async def yndx_callback(
    response: Response,
    code: str = Query(
        ...,
        title="code",
        description="Код подтверждения аутентификации в Yandex",
    ),
    auth_service: AuthService = Depends(get_auth_service),
    user_agent: Annotated[str | None, Header()] = None,
):
    client_id = settings.yndx_oauth.YNDX_CLIENT_ID
    client_secret = settings.yndx_oauth.YNDX_CLIENT_SECRET
    raw_str = f"{client_id}:{client_secret}"
    encoded_creds = b64encode(raw_str.encode()).decode()

    data = {"grant_type": "authorization_code", "code": code}

    headers = {
        "Content-type": "application/x-www-form-urlencoded",
        "Authorization": f"Basic {encoded_creds}",
    }

    token_resp = requests.post(
        url=settings.yndx_oauth.YNDX_TOKEN_URL, headers=headers, data=data
    )
    resp_dict = token_resp.json()
    logger.warning("Response YNDX_TOKEN_URL: %s", resp_dict)
    headers = {
        "Authorization": f"OAuth {resp_dict['access_token']}",
    }

    response_info = requests.get(
        url=settings.yndx_oauth.YNDX_INFO_URL, headers=headers
    )
    logger.warning("REsponse: %s", response_info.json())
    user_info = UserInfoSchema(**response_info.json())
    user, tokens = await auth_service.login_user_yndx(user_info, user_agent)

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

    return user


@router.post(
    "/token/refresh",
    status_code=status.HTTP_200_OK,
    response_model=UserTokenResponse,
    summary="New access and refresh tokens",
    description="Get new access and refresh tokens",
    responses=get_token_refr_response(),
)
async def refresh_token(
    request: Request,
    response: Response,
    user_id: str = Depends(get_user_id_from_refresh_token),
    user_agent: Annotated[str | None, Header()] = None,
    auth_service: AuthService = Depends(get_auth_service),
) -> UserTokenResponse:
    """
    Возвращает новую пару access_token/refresh_token токенов
    в обмен на корректный refresh_token
    """
    logger.info("token refresh from user_id %s", user_id)

    access_token = request.cookies.get("access_token")
    refresh_token = request.cookies.get("refresh_token")

    result = await auth_service.refresh_token(
        user_id, user_agent, access_token, refresh_token
    )

    response.set_cookie(
        key="access_token",
        value=result.access_token,
        httponly=True,
        samesite="lax",
    )
    response.set_cookie(
        key="refresh_token",
        value=result.refresh_token,
        httponly=True,
        samesite="lax",
    )

    return {
        "access_token": result.access_token,
        "refresh_token": result.refresh_token,
    }


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="User logout",
    description="User logout endpoint",
)
async def logout_user(
    request: Request,
    response: Response,
    user_id: str = Depends(get_user_id_from_access_token),
    user_agent: Annotated[str | None, Header()] = None,
    auth_service: AuthService = Depends(get_auth_service),
) -> None:
    """
    Выход пользователя - удаление токенов.
    """
    logger.info("logout user_id %s", user_id)

    access_token = request.cookies.get("access_token")
    refresh_token = request.cookies.get("refresh_token")

    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")

    await auth_service.logout_user(
        user_id, user_agent, access_token, refresh_token
    )

    return None


@router.post(
    "/password_update",
    status_code=status.HTTP_200_OK,
    summary="User password update",
    description="User password update endpoint",
    responses=get_change_psw_response(),
)
async def password_update(
    user_update: UserUpdate = Body(
        ...,
        description="creds for update password",
    ),
    user_id: str = Depends(get_user_id_from_access_token),
    auth_service: AuthService = Depends(get_auth_service),
) -> None:
    """
    Обновление пароля пользователя.
    """
    logger.info(
        "password_update for user %s %s (user_id %s)",
        user_update.first_name,
        user_update.last_name,
        user_id,
    )

    result = await auth_service.password_update(user_id, user_update)

    return result


@router.post(
    "/verify",
    response_model=BaseModel,
    status_code=status.HTTP_200_OK,
    summary="User permissions verify",
    description="User permissions verify endpoint",
)
async def verify_role(
    access_token: str = Query(description="Токен доступа"),
    role: str = Query(description="Имя роли"),
    auth_service: AuthService = Depends(get_auth_service),
) -> None:
    """
    Проверка наличия роли в пользовательском токене доступа.
    """
    result = await auth_service.verify_role(access_token, role)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Role {role} is not in token roles",
        )
    return None

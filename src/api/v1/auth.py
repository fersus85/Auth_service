import logging
from typing import Annotated

from fastapi import APIRouter, Body, Depends, Header, Request, Response, status
from pydantic import BaseModel

from responses.auth_responses import get_login_response, get_signup_response
from schemas.auth import UserLogin, UserLoginResponse
from schemas.user import UserCreate, UserRead, UserUpdate
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

    result = await auth_service.login_user(user_login, user_agent)

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
    "/social-login",
    response_model=BaseModel,
    status_code=status.HTTP_200_OK,
    summary="OAuth 2.0 login",
    description="OAuth 2.0 login",
)
async def social_login() -> BaseModel:
    return {}


@router.post(
    "/token/refresh",
    status_code=status.HTTP_200_OK,
    response_model=UserLoginResponse,
    summary="New access and refresh tokens",
    description="Get new access and refresh tokens",
)
async def refresh_token(
    request: Request,
    response: Response,
    user_id: str = Depends(get_user_id_from_refresh_token),
    user_agent: Annotated[str | None, Header()] = None,
    auth_service: AuthService = Depends(get_auth_service),
) -> UserLoginResponse:
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
)
async def password_update(
    user_update: UserUpdate,
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
async def verify_role() -> BaseModel:
    return {}

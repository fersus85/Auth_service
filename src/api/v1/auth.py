import logging
from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    Header,
    HTTPException,
    Request,
    Response,
    status,
)
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from db.casher import AbstractCache, get_cacher
from db.postrges_db.psql import get_db
from schemas.auth import UserLogin, UserLoginResponse
from schemas.user import UserCreate, UserRead, UserUpdate
from services.auth.auth_service import AuthService, get_auth_service
from services.role.role_service import RoleService, get_role_service
from services.utils import (
    get_user_id_from_access_token,
    get_user_id_from_refresh_token,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    response_model=BaseModel,
    summary="Temporary endpont for test",
    description="Temporary endpont for test",
)
async def auth(
    db: AsyncSession = Depends(get_db),
    cacher: AbstractCache = Depends(get_cacher),
):
    try:
        result = await db.execute(text("SELECT 1"))
        await cacher.set("Try", "probe", 180)
        data = await cacher.get("Try")
        value = result.scalar()
        return {
            "res": value,
            "msg": "Database connection is working!",
            "from_cache": data,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/signup",
    status_code=status.HTTP_201_CREATED,
    response_model=UserRead,
    summary="User registration",
    description="User registration endpoint",
)
async def signup_user(
    user_create: UserCreate,
    auth_service: AuthService = Depends(get_auth_service),
    role_service: RoleService = Depends(get_role_service),
) -> UserRead:
    """
    Регистрация нового пользователя
    """
    result = await auth_service.signup_user(user_create, role_service)
    logger.info(f"signup_user result = {result}")
    return result


@router.post(
    "/login",
    status_code=status.HTTP_200_OK,
    response_model=UserLoginResponse,
    summary="User login",
    description="User login endpoint returns access and refresh tokens",
)
async def login_user(
    user_login: UserLogin,
    response: Response,
    user_agent: Annotated[str | None, Header()] = None,
    auth_service: AuthService = Depends(get_auth_service),
) -> UserLoginResponse:
    """
    Аутентификация пользователя по логину и паролю.
    Выдача токенов.
    """
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
    result = await auth_service.password_update(user_id, user_update)
    logger.info(f"password_update result = {result}")
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

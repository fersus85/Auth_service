import logging

import jwt
from fastapi import Depends, HTTPException, status
from werkzeug.security import check_password_hash, generate_password_hash

from core.config import settings
from db.casher import AbstractCache, get_cacher
from exceptions.errors import PasswordOrLoginExc
from models.session import SessionHistoryChoices
from models.user import User
from schemas.auth import UserLogin, UserLoginResponse
from schemas.user import UserCreate, UserRead, UserUpdate
from services.auth import IAuthRepository
from services.auth.auth_repository import get_repository
from services.utils import decode_jwt_token, generate_new_tokens

logger = logging.getLogger(__name__)


class AuthService:
    """
    Сервисный класс для обработки аутентификации
        и авторизации пользователей.

    Этот класс предоставляет методы для регистрации пользователей,
    входа в систему, выхода, обновления токенов и управления паролями.
    Он взаимодействует с репозиторием для выполнения операций CRUD
    над данными пользователей и управляет сессиями и ролями пользователей.

    Атрибуты:
        repository (IAuthRepository): Интерфейс репозитория
            для операций с данными пользователей.
        cacher (AbstractCache): Интерфейс кэша
            для управления сессионными токенами.

    Методы:
        signup_user(user_create: UserCreate, role_service: RoleService)
            -> UserRead:
            Регистрирует нового пользователя и назначает роли.

        login_user(user_login: UserLogin, user_agent: str)
            -> UserLoginResponse:
            Аутентифицирует пользователя и возвращает токены доступа
                и обновления.

        logout_user(
            user_id: str,
            user_agent: str,
            access_token: str,
            refresh_token: str
        ) -> None:
            Выходит из системы пользователя, удаляя его активную сессию
            и добавляя токен доступа в черный список.

        refresh_token(
            user_id: str,
            user_agent: str,
            access_token: str,
            refresh_token: str
        ) -> UserLoginResponse:
            Выдает новые токены доступа и обновления для пользователя.

        password_update(user_id: str, user_update: UserUpdate) -> None:
            Обновляет пароль пользователя.

    Исключения:
        HTTPException: Поднимается при различных ошибках аутентификации,
        таких как неверные учетные данные или проблемы с управлением токенами.
    """

    def __init__(
        self,
        repository: IAuthRepository,
        cacher: AbstractCache,
    ):
        self.repository = repository
        self.cacher = cacher

    async def signup_user(self, user_create: UserCreate) -> UserRead:
        """
        Регистрация пользователя.
        """

        user_create_dict = user_create.model_dump()

        password = user_create_dict.pop("password")

        if len(password) < 8 or len(user_create_dict["login"]) < 3:
            raise PasswordOrLoginExc()

        user_create_dict["password_hash"] = generate_password_hash(password)

        created_user = await self.repository.create_user(
            User(**user_create_dict)
        )
        return created_user

    async def login_user(
        self, user_login: UserLogin, user_agent: str
    ) -> UserLoginResponse:
        """
        Аутентификация пользователя логином и паролем.
        """
        user = await self.repository.get_user_by_login(user_login.login)

        if not user:
            logger.error("User %s not found", user_login.login)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid login or password",
            )

        if not check_password_hash(user.password_hash, user_login.password):
            logger.error("Password is incorrect")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid login or password",
            )

        (
            access_token_encoded_jwt,
            refresh_token_encoded_jwt,
        ) = await generate_new_tokens(user.id)

        await self.repository.delete_active_session(user.id, user_agent)

        await self.repository.insert_new_active_session(
            user.id, user_agent, refresh_token_encoded_jwt
        )
        await self.repository.insert_event_to_session_hist(
            user.id,
            user_agent,
            refresh_token_encoded_jwt,
            SessionHistoryChoices.LOGIN_WITH_PASSWORD,
        )

        return UserLoginResponse(
            access_token=access_token_encoded_jwt,
            refresh_token=refresh_token_encoded_jwt,
        )

    async def logout_user(
        self,
        user_id: str,
        user_agent: str,
        access_token: str,
        refresh_token: str,
    ) -> None:
        """
        Выход пользователя.
        """
        await self.repository.delete_active_session(user_id, user_agent)

        await self._blacklist_access_token(access_token)

        await self.repository.insert_event_to_session_hist(
            user_id,
            user_agent,
            refresh_token,
            SessionHistoryChoices.USER_LOGOUT,
        )

        return None

    async def refresh_token(
        self,
        user_id: str,
        user_agent: str,
        access_token: str,
        refresh_token: str,
    ) -> UserLoginResponse:
        """
        Выдача новых токенов пользователю.
        """
        check = await self.repository.check_refresh_token_in_active_session(
            user_id, user_agent, refresh_token
        )
        if not check:
            logger.error("Refresh token is invalid")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token is invalid",
            )

        await self.repository.delete_active_session(user_id, user_agent)

        await self._blacklist_access_token(access_token)

        (
            access_token_encoded_jwt,
            refresh_token_encoded_jwt,
        ) = await generate_new_tokens(user_id)

        await self.repository.insert_new_active_session(
            user_id, user_agent, refresh_token_encoded_jwt
        )

        await self.repository.insert_event_to_session_hist(
            user_id,
            user_agent,
            refresh_token,
            SessionHistoryChoices.REFRESH_TOKEN_UPDATE,
        )

        return UserLoginResponse(
            access_token=access_token_encoded_jwt,
            refresh_token=refresh_token_encoded_jwt,
        )

    async def password_update(
        self,
        user_id: str,
        user_update: UserUpdate,
    ) -> None:
        """
        Смена пароля пользователю.
        """
        if not user_update.password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New password is empty!",
            )

        if len(user_update.password) < 8:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password length must be 8 or more characters",
            )

        new_password_hash = generate_password_hash(user_update.password)

        await self.repository.update_passord_hash(
            user_id,
            new_password_hash,
        )

        return None

    async def _blacklist_access_token(self, encoded_jwt_token: str):
        """
        Добавление access_token в чёрный список в Redis.
        """
        try:
            access_token_dict = await decode_jwt_token(encoded_jwt_token)
        except jwt.exceptions.PyJWTError:
            return None

        access_token_id = access_token_dict["jti"]
        await self.cacher.set(
            f"blacklist:{access_token_id}",
            access_token_dict["user_id"],
            settings.JWT_TOKEN_EXPIRE_TIME_M * 60,
        )


def get_auth_service(
    repository: IAuthRepository = Depends(get_repository),
    cacher: AbstractCache = Depends(get_cacher),
) -> AuthService:
    """
    Функция для создания экземпляра класса AuthService
    """
    return AuthService(repository=repository, cacher=cacher)

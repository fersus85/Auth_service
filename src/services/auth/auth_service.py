import logging

from fastapi import Depends, HTTPException, status
from werkzeug.security import check_password_hash, generate_password_hash

from core.config import settings
from db.casher import AbstractCache, get_cacher
from models.session import SessionHistoryChoices
from models.user import User
from schemas.auth import UserLogin, UserLoginResponse
from schemas.user import UserCreate, UserRead, UserUpdate
from services.auth import IAuthRepository
from services.auth.auth_repository import get_repository
from services.role.role_service import RoleService
from services.utils import decode_jwt_token, generate_new_tokens

logger = logging.getLogger(__name__)


class AuthService:

    def __init__(
        self,
        repository: IAuthRepository,
        cacher: AbstractCache,
    ):
        self.repository = repository
        self.cacher = cacher

    async def signup_user(
        self, user_create: UserCreate, role_service: RoleService
    ) -> UserRead:
        """
        Регистрация пользователя.
        """
        user_create_dict = user_create.model_dump()

        password = user_create_dict.pop("password")
        user_create_dict["password_hash"] = generate_password_hash(password)

        role_names = list(user_create_dict.pop("roles"))
        role_names.append("user")
        role_id_list = await self._get_role_ids_from_names(
            set(role_names), role_service
        )

        user = User(**user_create_dict)

        created_user = await self.repository.create_user(user)
        await self.repository.assign_roles_to_user(created_user, role_id_list)

        return user

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

        (access_token_encoded_jwt, refresh_token_encoded_jwt) = (
            await generate_new_tokens(user.id)
        )

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

        (access_token_encoded_jwt, refresh_token_encoded_jwt) = (
            await generate_new_tokens(user_id)
        )

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
        except Exception:
            return None

        access_token_id = access_token_dict["jti"]
        await self.cacher.set(
            f"blacklist:{access_token_id}",
            access_token_dict["user_id"],
            settings.JWT_TOKEN_EXPIRE_TIME_M * 60,
        )

    async def _get_role_ids_from_names(
        self, role_names: list, role_service: RoleService
    ):
        """
        Получение списка ID ролей по списку имён ролей
        через сервис ролей
        """
        role_id_list = []
        for role_name in role_names:
            role = await role_service.get_by_name(role_name)
            if role:
                role_id_list.append(role.id)

        return role_id_list


def get_auth_service(
    repository: IAuthRepository = Depends(get_repository),
    cacher: AbstractCache = Depends(get_cacher),
) -> AuthService:
    """
    Функция для создания экземпляра класса AuthService
    """
    return AuthService(repository=repository, cacher=cacher)

import logging
from contextlib import suppress

import jwt
from fastapi import Depends
from werkzeug.security import check_password_hash, generate_password_hash

from core.config import UserRoleDefault, settings
from db.casher import AbstractCache, get_cacher
from exceptions.errors import PasswordOrLoginExc, UnauthorizedExc
from models.session import SessionHistoryChoices
from models.user import User
from schemas.auth import UserLogin, UserLoginResponse, UserTokenResponse
from schemas.user import UserBase, UserCreate, UserRead, UserRole, UserUpdate
from schemas.yndx_oauth import UserInfoSchema
from services.auth import IAuthRepository
from services.auth.auth_repository import get_repository
from services.helpers import generate_secure_password
from services.tracer import Tracer, get_tracer
from services.user.user_service import UserService, get_user_service
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
        user_service (UserService): Сервис пользователей, для получения ролей

    Методы:
        signup_user(user_create: UserCreate, role_service: RoleService)
            -> UserRead:
            Регистрирует нового пользователя и назначает роли.

        login_user(user_login: UserLogin, user_agent: str)
            -> tuple[UserRole, UserTokenResponse:
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
        ) -> UserTokenResponse:
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
        user_service: UserService,
        tracer: Tracer,
    ):
        self.repository = repository
        self.cacher = cacher
        self.user_service = user_service
        self.tracer = tracer

    async def signup_user(self, user_create: UserCreate) -> UserRead:
        """
        Регистрация пользователя.
        """
        with self.tracer.start_span("auth_service.signup_user") as span:
            span.set_attribute("login", user_create.login)
            user_create_dict = user_create.model_dump()

            password = user_create_dict.pop("password")

            if len(password) < 8 or len(user_create_dict["login"]) < 3:
                raise PasswordOrLoginExc()

            user_create_dict["password_hash"] = generate_password_hash(
                password
            )

            created_user = await self.repository.create_user(
                User(**user_create_dict)
            )
            return created_user

    async def get_token(
        self, user: UserRole, user_agent: str
    ) -> tuple[UserRole, UserTokenResponse]:
        """
        Генерирует новые токены доступа и обновления для пользователя,
        удаляет активную сессию и создает новую сессию.

        Args:
            user (UserRole): Объект, представляющий пользователя,
                            содержащий информацию о его идентификаторе и роли.
            user_agent (str): Строка, представляющая информацию о клиенте
                            (браузере или приложении) пользователя.

        Returns:
            tuple[UserRole, UserTokenResponse]: Кортеж, содержащий:
                - UserLoginResponse: Объект с информацией о пользователе.
                - UserTokenResponse: Объект с токенами доступа и обновления.
        """
        (
            access_token_encoded_jwt,
            refresh_token_encoded_jwt,
        ) = await generate_new_tokens(user.id, user.role)

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

        return (
            UserLoginResponse(
                id=user.id,
                first_name=user.first_name,
                last_name=user.last_name,
                role=user.role,
            ),
            UserTokenResponse(
                access_token=access_token_encoded_jwt,
                refresh_token=refresh_token_encoded_jwt,
            ),
        )

    async def login_user(
        self, user_login: UserLogin, user_agent: str
    ) -> tuple[UserRole, UserTokenResponse]:
        """
        Аутентификация пользователя логином и паролем.
        """
        user = await self.repository.get_user_with_roles_by_login(
            user_login.login
        )

        if not user:
            logger.error("User %s not found", user_login.login)
            raise UnauthorizedExc("Invalid login or password")

        if not check_password_hash(user.password_hash, user_login.password):
            logger.error("Password is incorrect")
            raise UnauthorizedExc("Invalid login or password")

        user_resp, token_resp = await self.get_token(user, user_agent)

        return user_resp, token_resp

    async def login_user_yndx(
        self, user_info: UserInfoSchema, user_agent: str, request_id: str
    ) -> tuple[UserLoginResponse, UserTokenResponse]:
        """
        Аутентификация пользователя логином и паролем.
        Если пользователь не существует, он будет создан с автоматически
        сгенерированным паролем.

        Параметры:
        user_info (UserInfoSchema): Информация о пользователе
        user_agent (str): Информация о клиенте, который выполняет запрос.

        Возвращает:
        tuple[UserLoginResponse, UserTokenResponse]: Информация о
        пользователе и токены
        """
        with self.tracer.start_span("auth_service.login_user_yndx") as span:
            span.set_attribute("user_login", user_info.login)
            span.set_attribute("http.request_id", request_id)
            user: UserRole = await self.repository.get_user_by_login(
                user_info.login
            )
            with self.tracer.start_span("get_user_by_login") as inner_span:
                inner_span.set_attribute("http.request_id", request_id)
                user: UserRole = await self.repository.get_user_by_login(
                    user_info.login
                )
                if user:
                    inner_span.set_attribute("user_exists", True)
                    logger.warning("User %s exists, updating", user_info.login)
                    await self.repository.update_user(user, user_info)
                else:
                    inner_span.set_attribute("user_create", False)
                    logger.warning("User %s creating", user_info.login)
                    # TODO пароль отправлять на почту пользователя
                    psw = generate_secure_password()
                    new_user = UserCreate(
                        login=user_info.login,
                        first_name=user_info.first_name,
                        last_name=user_info.last_name,
                        password=psw,
                    )
                    await self.signup_user(new_user)

            with self.tracer.start_span(
                "get_user_with_roles_by_login"
            ) as inner_span:
                inner_span.set_attribute("http.request_id", request_id)
                login_user = (
                    await self.repository.get_user_with_roles_by_login(
                        user_info.login
                    )
                )

            with self.tracer.start_span("get_token") as inner_span:
                inner_span.set_attribute("http.request_id", request_id)
                user_resp, token_resp = await self.get_token(
                    login_user, user_agent
                )

            return user_resp, token_resp

    async def login_user_oauth(
        self, user: UserBase, user_agent: str, request_id: str
    ) -> tuple[UserLoginResponse, UserTokenResponse]:
        """
        Аутентификация пользователя логином и паролем.
        Если пользователь не существует, он будет создан с автоматически
        сгенерированным паролем.

        Параметры:
        user_info (UserBase): Информация о пользователе
        user_agent (str): Информация о клиенте, который выполняет запрос.

        Возвращает:
        tuple[UserLoginResponse, UserTokenResponse]: Информация о
        пользователе и токены
        """
        user_info = UserInfoSchema(
            login=user.login,
            first_name=user.first_name,
            last_name=user.last_name,
            display_name="",
            real_name="",
            sex="",
            id="",
            client_id="",
            psuid="",
        )

        return await self.login_user_yndx(user_info, user_agent, request_id)

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
    ) -> UserTokenResponse:
        """
        Выдача новых токенов пользователю.
        """
        check = await self.repository.check_refresh_token_in_active_session(
            user_id, user_agent, refresh_token
        )
        if not check:
            logger.error("Refresh token is invalid")
            raise UnauthorizedExc("Refresh token is invalid")

        await self.repository.delete_active_session(user_id, user_agent)

        await self._blacklist_access_token(access_token)

        user_role = await self.repository.get_user_roles(user_id)
        (
            access_token_encoded_jwt,
            refresh_token_encoded_jwt,
        ) = await generate_new_tokens(user_id, user_role)

        await self.repository.insert_new_active_session(
            user_id, user_agent, refresh_token_encoded_jwt
        )

        await self.repository.insert_event_to_session_hist(
            user_id,
            user_agent,
            refresh_token,
            SessionHistoryChoices.REFRESH_TOKEN_UPDATE,
        )

        return UserTokenResponse(
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
            raise PasswordOrLoginExc()

        if len(user_update.password) < 8:
            raise PasswordOrLoginExc()

        new_password_hash = generate_password_hash(user_update.password)

        await self.repository.update_passord_hash(
            user_id,
            new_password_hash,
        )

        return None

    async def verify_role(self, access_token: str, role: str) -> bool:
        """
        Проверка наличия роли в пользовательском токене доступа.
        """
        access_token_dict: dict = await decode_jwt_token(access_token)
        token_role: str = access_token_dict.get("role", None)

        priority = list(UserRoleDefault)

        with suppress(KeyError, ValueError):
            required_access_lvl = priority.index(UserRoleDefault(role))
            user_access_lvl = priority.index(UserRoleDefault(token_role))

            if required_access_lvl >= user_access_lvl:
                return True

        return False

    async def delete_user(self, user_id: str) -> None:
        """
        Удаление пользователя.
        """
        await self.repository.delete_user(user_id)

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
    user_service: UserService = Depends(get_user_service),
    tracer: Tracer = Depends(get_tracer),
) -> AuthService:
    """
    Функция для создания экземпляра класса AuthService
    """
    return AuthService(
        repository=repository,
        cacher=cacher,
        user_service=user_service,
        tracer=tracer,
    )

import logging
from datetime import datetime, timedelta
from uuid import UUID, uuid4

import jwt
from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import delete, insert, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from werkzeug.security import check_password_hash, generate_password_hash

from db.casher import AbstractCache, get_cacher
from db.postrges_db.psql import get_db
from models.session import ActiveSession, SessionHistory, SessionHistoryChoices
from models.user import Role, User
from schemas.auth import UserLogin, UserLoginResponse
from schemas.user import UserCreate, UserRead
from services.role.role_service import RoleService

logger = logging.getLogger(__name__)

# перенести в Settings
SECRET_KEY = "123qwerty"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_TIME_M = 15


class AuthService:

    def __init__(
        self,
        db: AsyncSession,
        cacher: AbstractCache,
    ):
        self.db = db
        self.cacher = cacher

    async def signup_user(
        self, user_create: UserCreate, role_service: RoleService
    ) -> UserRead:

        user_create_dict = user_create.model_dump()

        # Женя, прости за комментарии!
        # заменяем поле с паролем на поле с хэшем пароля
        password = user_create_dict.pop("password")
        user_create_dict["password_hash"] = generate_password_hash(password)

        # формируем список ID ролей из списка имён ролей
        role_id_list = await self._get_role_ids_from_names(
            user_create_dict.pop("roles"), role_service
        )

        user = User(**user_create_dict)

        user = await self._add_user_to_db(user, role_id_list)

        return user

    async def login_user(
        self, user_login: UserLogin, user_agent: str
    ) -> UserLoginResponse:

        logger.info(
            f"login_user: {user_login.login}, user_agent: {user_agent}"
        )

        user = await self._get_user_by_login(user_login.login)

        if not user:
            logger.error(f"User {user_login.login} not found")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"User {user_login.login} not found",
            )

        if not check_password_hash(user.password_hash, user_login.password):
            logger.error(f"Password is incorrect")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Password is incorrect",
            )

        # генерируем новую пару токенов
        (access_token_encoded_jwt, refresh_token_encoded_jwt) = (
            await self._generate_new_tokens(user.id)
        )

        # удаляем другие активные сессии с этого же девайса
        await self._delete_active_session(user.id, user_agent)

        # вставляем инф-ию о новой сессии
        await self._insert_new_active_session(
            user.id, user_agent, refresh_token_encoded_jwt
        )
        await self._insert_event_to_session_hist(
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

        logger.info(
            f"logout_user, user_id: {user_id}, user_agent: {user_agent}"
        )

        # удаляем активные сессии с этого девайса
        await self._delete_active_session(user_id, user_agent)

        # добавляем access_token в чёрный список в Redis
        await self._blacklist_access_token(access_token)

        # логгируем событие выхода
        await self._insert_event_to_session_hist(
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

        logger.info(
            f"refresh_token, user_id: {user_id}, user_agent: {user_agent}"
        )

        # проверяем, что данный refresh_token действительно есть в БД
        check = await self._check_refresh_token_in_active_session(
            user_id, user_agent, refresh_token
        )
        if not check:
            logger.error(f"Refresh token is invalid")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Refresh token is invalid",
            )

        # удаляем активные сессии с этого девайса (удаляем refresh_token)
        await self._delete_active_session(user_id, user_agent)

        # добавляем старый access_token в чёрный список в Redis (это надо?)
        await self._blacklist_access_token(access_token)

        # генерируем новую пару токенов
        (access_token_encoded_jwt, refresh_token_encoded_jwt) = (
            await self._generate_new_tokens(user_id)
        )

        # вставляем инф-ию о новой сессии
        await self._insert_new_active_session(
            user_id, user_agent, refresh_token_encoded_jwt
        )

        # логгируем событие рефреша
        await self._insert_event_to_session_hist(
            user_id,
            user_agent,
            refresh_token,
            SessionHistoryChoices.REFRESH_TOKEN_UPDATE,
        )

        return UserLoginResponse(
            access_token=access_token_encoded_jwt,
            refresh_token=refresh_token_encoded_jwt,
        )

    async def _check_refresh_token_in_active_session(
        self, user_id: UUID, user_agent: str, refresh_token: str
    ):
        refresh_token_dict = await self._decode_jwt_token(refresh_token)
        refresh_token_id = refresh_token_dict["jti"]

        stmt = select(ActiveSession).where(
            ActiveSession.user_id == user_id
            and ActiveSession.refresh_token_id == refresh_token_id
        )
        sess = await self.db.scalar(stmt)

        if not sess:
            return False

        return True

    async def _get_user_by_login(self, login: str) -> User:

        stmt = select(User).where(User.login == login)
        user = await self.db.scalar(stmt)
        return user

    async def _delete_active_session(
        self, user_id: str, user_agent: str
    ) -> None:

        # удаляем другие активные сессии с этого же девайса
        stmt = delete(ActiveSession).where(
            ActiveSession.user_id == user_id
            and ActiveSession.device_info == user_agent
        )
        await self.db.execute(stmt)
        await self.db.commit()

    async def _generate_new_tokens(self, user_id: UUID):

        now = datetime.now()
        expire_for_access_token = now + timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_TIME_M
        )
        expire_for_refresh_token = now + timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_TIME_M * 100
        )

        access_token_dict = {
            "user_id": str(user_id),
            "iat": now.timestamp(),
        }
        refresh_token_dict = access_token_dict.copy()

        access_token_dict.update(
            {"jti": str(uuid4()), "exp": expire_for_access_token}
        )
        refresh_token_dict.update(
            {"jti": str(uuid4()), "exp": expire_for_refresh_token}
        )

        access_token_encoded_jwt = jwt.encode(
            access_token_dict, SECRET_KEY, algorithm=ALGORITHM
        )
        refresh_token_encoded_jwt = jwt.encode(
            refresh_token_dict, SECRET_KEY, algorithm=ALGORITHM
        )

        return (access_token_encoded_jwt, refresh_token_encoded_jwt)

    async def _decode_jwt_token(self, encoded_jwt_token: str):
        token_dict = jwt.decode(
            encoded_jwt_token, SECRET_KEY, algorithms=[ALGORITHM]
        )
        return token_dict

    async def _insert_new_active_session(
        self, user_id: UUID, user_agent: str, refresh_token_encoded_jwt: str
    ):

        refresh_token_dict = await self._decode_jwt_token(
            refresh_token_encoded_jwt
        )

        session_dict = {
            "user_id": user_id,
            "refresh_token_id": refresh_token_dict["jti"],
            "issued_at": datetime.fromtimestamp(refresh_token_dict["iat"]),
            "expires_at": datetime.fromtimestamp(refresh_token_dict["exp"]),
            "device_info": user_agent,
        }

        session = ActiveSession(**session_dict)
        self.db.add(session)
        await self.db.commit()

        return None

    async def _blacklist_access_token(self, encoded_jwt_token: str):

        access_token_dict = await self._decode_jwt_token(encoded_jwt_token)

        access_token_id = access_token_dict["jti"]
        await self.cacher.set(
            f"blacklist:{access_token_id}",
            access_token_dict["user_id"],
            ACCESS_TOKEN_EXPIRE_TIME_M * 60,
        )

    async def _insert_event_to_session_hist(
        self,
        user_id: UUID,
        user_agent: str,
        refresh_token_encoded_jwt: str,
        event: SessionHistoryChoices,
    ):

        refresh_token_dict = await self._decode_jwt_token(
            refresh_token_encoded_jwt
        )

        session_dict = {
            "user_id": user_id,
            "refresh_token_id": refresh_token_dict["jti"],
            "issued_at": datetime.fromtimestamp(refresh_token_dict["iat"]),
            "expires_at": datetime.fromtimestamp(refresh_token_dict["exp"]),
            "device_info": user_agent,
            "name": event,
        }

        session_hist = SessionHistory(**session_dict)
        self.db.add(session_hist)
        await self.db.commit()
        return None

    async def _get_role_ids_from_names(
        self, role_names: list, role_service: RoleService
    ):

        role_id_list = []
        for role_name in role_names:
            logger.info(f"role_name: {role_name}")
            role = await role_service.get_by_name(role_name)
            if role:
                role_id_list.append(role.id)

        return role_id_list

    async def _add_user_to_db(self, user: User, role_id_list: list):

        try:
            self.db.add(user)
            await self.db.commit()
            await self.db.refresh(user)
        except IntegrityError as e:
            logger.error(str(e))
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"User {user.login} already exists",
            )

        # присваиваем юзеру указанные роли путём вставки связей в content.user_roles
        for role_id in role_id_list:
            try:
                stmt = insert(
                    Role.__table__.metadata.tables["content.user_roles"]
                ).values(role_id=role_id, user_id=user.id)
                await self.db.execute(stmt)
                await self.db.commit()
            except Exception as e:
                logger.error(str(e))

        return user


def get_auth_service(
    db: AsyncSession = Depends(get_db),
    cacher: AbstractCache = Depends(get_cacher),
) -> AuthService:
    """
    Функция для создания экземпляра класса AuthService
    """
    return AuthService(db=db, cacher=cacher)


def get_access_token_from_cookies(request: Request):

    token = request.cookies.get("access_token")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token not found",
        )

    return token


async def get_user_id_from_access_token(
    access_token: str = Depends(get_access_token_from_cookies),
):

    try:
        payload = jwt.decode(access_token, SECRET_KEY, algorithms=ALGORITHM)
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Токен не валидный!",
        )

    expire = payload.get("exp")
    expire_time = datetime.fromtimestamp(int(expire))
    if (not expire) or (expire_time < datetime.now()):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Токен истек"
        )

    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Не найден ID пользователя",
        )

    return user_id


def get_refresh_token_from_cookies(request: Request):

    token = request.cookies.get("refresh_token")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found",
        )

    return token


async def get_user_id_from_refresh_token(
    refresh_token: str = Depends(get_refresh_token_from_cookies),
):

    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=ALGORITHM)
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Токен не валидный!",
        )

    expire = payload.get("exp")
    expire_time = datetime.fromtimestamp(int(expire))
    if (not expire) or (expire_time < datetime.now()):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Токен истек"
        )

    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Не найден ID пользователя",
        )

    return user_id

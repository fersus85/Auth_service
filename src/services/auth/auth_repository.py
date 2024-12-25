import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, List, Type
from uuid import UUID

from fastapi import Depends
from sqlalchemy import and_, delete, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from core.config import UserRoleDefault
from models import Role, User
from models.session import ActiveSession, SessionHistory, SessionHistoryChoices
from schemas.user import UserRead, UserRole
from schemas.yndx_oauth import UserInfoSchema
from services import get_data_access
from services.auth import IAuthRepository, get_auth_repository_class
from services.utils import decode_jwt_token


class AuthServiceExc(Exception):
    pass


logger = logging.getLogger(__name__)


class SQLAlchemyAuthRepository(IAuthRepository):
    def __init__(self, db_session: AsyncSession):
        """
        Инициализация сервиса аутентификации сессией SQLAlchemy,
        связанной с таблицей roles
        """
        self.db_session = db_session

    @asynccontextmanager
    async def _transaction_handler(self, error_message: str):
        try:
            yield
            await self.db_session.commit()
        except IntegrityError as e:
            logger.error(e)
            await self.db_session.rollback()
            raise

    async def create_user(self, user: User) -> UserRead:
        """
        Создаёт нового пользователя с ролью user

        :param to_create: Схема на основе которой
            нужно создать нового пользователя
        """

        stmt = select(Role).where(Role.name == UserRoleDefault.USER)
        role_instance = await self.db_session.scalar(stmt)
        user.roles.append(role_instance)

        async with self._transaction_handler("Can't create new user"):
            self.db_session.add(user)

        return UserRead.model_validate(user)

    async def update_user(
        self, user_db: User, user_info: UserInfoSchema
    ) -> UserRead:
        """
        Обновляет информацию о пользователе.

        :param user_db: Существующий пользователь из базы данных.
        :param user_info: Схема с новой информацией о пользователе.
        :return: Обновленная информация о пользователе.
        """
        user_db.first_name = user_info.first_name
        user_db.last_name = user_info.last_name
        await self.db_session.commit()
        return UserRead.model_validate(user_db)

    async def get_user_by_login(self, login: str) -> User:
        """
        Находит и возвращает пользователя по его логину.

        :param login: Логин пользователя
        """
        stmt = select(User).where(User.login == login)
        user = await self.db_session.scalar(stmt)
        return user

    async def get_user_with_roles_by_login(
        self, login: str
    ) -> UserRole | None:
        """
        Получение данных о пользователе с ролями по логину
        """
        stmt = (
            select(User)
            .options(joinedload(User.roles))
            .where(User.login == login)
        )
        user = await self.db_session.scalar(stmt)
        if not user:
            return None

        role = next((role.name for role in user.roles), None)

        return UserRole(
            id=user.id,
            first_name=user.first_name,
            last_name=user.last_name,
            login=user.login,
            password_hash=user.password_hash,
            role=role,
        )

    async def get_user_roles(self, id: str) -> List[str]:
        """
        Получение ролей пользователя по логину
        """
        stmt = select(Role.name).join(User.roles).where(User.id == id)
        result = await self.db_session.scalars(stmt)

        return result.first() or []

    async def check_refresh_token_in_active_session(
        self, user_id: UUID, user_agent: str, refresh_token: str
    ) -> bool:
        """
        Проверяет наличие refresh токена в списке активных сессий в БД

        :param user_id: ID пользователя
        :param user_agent: девайс пользователя
        :param refresh_token: закодированный токен
        """
        refresh_token_dict = await decode_jwt_token(refresh_token)
        refresh_token_id = refresh_token_dict["jti"]

        stmt = select(ActiveSession).where(
            and_(
                ActiveSession.user_id == user_id,
                ActiveSession.refresh_token_id == refresh_token_id,
            )
        )
        sess = await self.db_session.scalar(stmt)

        if not sess:
            return False

        return True

    async def insert_new_active_session(
        self, user_id: UUID, user_agent: str, refresh_token: str
    ) -> None:
        """
        Добавляет новую активную сессию с refresh токеном в БД

        :param user_id: ID пользователя
        :param user_agent: девайс пользователя
        :param refresh_token: закодированный токен
        """

        refresh_token_dict = await decode_jwt_token(refresh_token)

        session_dict = {
            "user_id": user_id,
            "refresh_token_id": refresh_token_dict["jti"],
            "issued_at": datetime.fromtimestamp(refresh_token_dict["iat"]),
            "expires_at": datetime.fromtimestamp(refresh_token_dict["exp"]),
            "device_info": user_agent,
        }

        session = ActiveSession(**session_dict)

        async with self._transaction_handler("Can't create new session"):
            self.db_session.add(session)

        return None

    async def delete_active_session(
        self, user_id: str, user_agent: str
    ) -> None:
        """
        Удаляет активную сессию заданного пользователя/девайса

        :param user_id: ID пользователя
        :param user_agent: девайс пользователя
        """
        # удаляем другие активные сессии с этого же девайса
        stmt = delete(ActiveSession).where(
            and_(
                ActiveSession.user_id == user_id,
                ActiveSession.device_info == user_agent,
            )
        )
        res = await self.db_session.execute(stmt)
        if res.rowcount == 0:
            logger.warning(
                "Delete operation ActiveSession failed %s %s",
                user_id,
                user_agent,
            )

    async def insert_event_to_session_hist(
        self,
        user_id: UUID,
        user_agent: str,
        refresh_token: str,
        event: SessionHistoryChoices,
    ) -> None:
        """
        Добавляет событие в историю сессий

        :param user_id: ID пользователя
        :param user_agent: девайс пользователя
        :param refresh_token: закодированный токен
        """
        refresh_token_dict = await decode_jwt_token(refresh_token)

        session_dict = {
            "user_id": user_id,
            "refresh_token_id": refresh_token_dict["jti"],
            "issued_at": datetime.fromtimestamp(refresh_token_dict["iat"]),
            "expires_at": datetime.fromtimestamp(refresh_token_dict["exp"]),
            "device_info": user_agent,
            "name": event,
        }

        session_hist = SessionHistory(**session_dict)

        async with self._transaction_handler("Can't add session event"):
            self.db_session.add(session_hist)

    async def update_passord_hash(
        self,
        user_id: UUID,
        new_password_hash: str,
    ) -> None:
        """
        Обновляет хэш пароля пользователя

        :param user_id: ID пользователя
        :param new_password_hash: новый хэш пароля
        """
        stmt = (
            update(User)
            .returning(User)
            .where(User.id == user_id)
            .values(password_hash=new_password_hash)
        )
        async with self._transaction_handler("Can't update user"):
            await self.db_session.execute(stmt)


async def get_repository(
    data_access: Any = Depends(get_data_access),
    auth_repository_class: Type[IAuthRepository] = Depends(
        get_auth_repository_class
    ),
) -> IAuthRepository:
    return auth_repository_class(data_access)

import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, List, Type
from uuid import UUID

from fastapi import Depends
from sqlalchemy import and_, delete, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from models import Role, User
from models.session import ActiveSession, SessionHistory, SessionHistoryChoices
from schemas.user import UserRead
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
            raise AuthServiceExc(error_message) from e

    async def create_user(self, user: User) -> UserRead:
        """
        Создаёт нового пользователя

        :param to_create: Схема на основе которой
            нужно создать нового пользователя
        """

        async with self._transaction_handler("Can't create new user"):
            self.db_session.add(user)

        return UserRead.model_validate(user)

    async def assign_roles_to_user(
        self, user: User, role_ids: List
    ) -> UserRead:
        """
        Назначает пользователю роли из списка ID ролей.

        :param user: Пользователь
        :param role_ids: Список ID ролей
        """
        if not role_ids:
            return None

        role_mappings = [
            {"role_id": role_id, "user_id": user.id} for role_id in role_ids
        ]

        async with self._transaction_handler("Can't assign roles"):
            await self.db_session.execute(
                Role.__table__.metadata.tables["content.user_roles"].insert(),
                role_mappings,
            )
        return None

    async def get_user_by_login(self, login: str) -> User:
        """
        Находит и возвращает пользователя по его логину.

        :param login: Логин пользователя
        """
        stmt = select(User).where(User.login == login)
        user = await self.db_session.scalar(stmt)
        return user

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
        async with self._transaction_handler("Can't create delete session"):
            await self.db_session.execute(stmt)

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

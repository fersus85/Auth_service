import logging
from contextlib import asynccontextmanager
from typing import Any, List, Type

from fastapi import Depends
from sqlalchemy import and_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from models import User
from models.session import SessionHistory, SessionHistoryChoices
from schemas.session import HistoryRead
from schemas.user import UserRead
from services import get_data_access
from services.user import IUserRepository, get_user_repository_class


class UserServiceExc(Exception):
    pass


logger = logging.getLogger(__name__)


class SQLAlchemyUserRepository(IUserRepository):
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
            raise UserServiceExc(error_message) from e

    async def get_profile(self, user_id: str) -> UserRead:
        """
        Получение данных о пользователе

        :param user_id: ID пользователя
        """
        stmt = select(User).where(User.id == user_id)
        user = await self.db_session.scalar(stmt)
        return user

    async def get_history(self, user_id: str) -> List[HistoryRead]:
        """
        Получение истории логинов пользователя

        :param user_id: ID пользователя
        """
        stmt = (
            select(SessionHistory)
            .where(
                and_(
                    SessionHistory.user_id == user_id,
                    SessionHistory.name
                    == SessionHistoryChoices.LOGIN_WITH_PASSWORD,
                )
            )
            .order_by(SessionHistory.created_at)
        )
        result = await self.db_session.scalars(stmt)
        sess_hist = [HistoryRead.model_validate(row) for row in result]
        return sess_hist


async def get_repository(
    data_access: Any = Depends(get_data_access),
    user_repository_class: Type[IUserRepository] = Depends(
        get_user_repository_class
    ),
) -> IUserRepository:
    return user_repository_class(data_access)

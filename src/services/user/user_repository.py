import logging
from contextlib import asynccontextmanager
from typing import Any, Type

from fastapi import Depends
from sqlalchemy import and_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from models import User
from models.session import SessionHistory, SessionHistoryChoices
from schemas.session import HistoryBase, HistoryRead
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
            raise

    async def get_profile(self, user_id: str) -> UserRead:
        """
        Получение данных о пользователе

        :param user_id: ID пользователя
        """
        stmt = select(User).where(User.id == user_id)
        user = await self.db_session.scalar(stmt)
        return user

    async def get_history(
        self, user_id: str, page_size: int, page_number: int
    ) -> HistoryRead:
        """
        Получение истории логинов пользователя

        :param user_id: ID пользователя
        :page_size: int Кол-во событий настранице
        :page_number: int Номер страницы
        """

        stmt = select(SessionHistory).where(
            and_(
                SessionHistory.user_id == user_id,
                SessionHistory.name
                == SessionHistoryChoices.LOGIN_WITH_PASSWORD,
            )
        )

        result_total = await self.db_session.scalars(stmt)
        sess_hist_total = [
            HistoryBase.model_validate(row) for row in result_total
        ]
        total = len(sess_hist_total)

        stmt = (
            stmt.order_by(SessionHistory.created_at)
            .limit(page_size)
            .offset((page_number - 1) * page_size)
        )

        result = await self.db_session.scalars(stmt)
        sess_hist = [HistoryBase.model_validate(row) for row in result]

        return HistoryRead(
            total=total,
            page_number=page_number,
            page_size=page_size,
            results=sess_hist,
        )


async def get_repository(
    data_access: Any = Depends(get_data_access),
    user_repository_class: Type[IUserRepository] = Depends(
        get_user_repository_class
    ),
) -> IUserRepository:
    return user_repository_class(data_access)

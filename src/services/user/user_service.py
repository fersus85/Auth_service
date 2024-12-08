import logging
from typing import List

from fastapi import Depends
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from db.casher import AbstractCache, get_cacher
from db.postrges_db.psql import get_db
from models.session import SessionHistory, SessionHistoryChoices
from models.user import User
from schemas.session import HistoryRead
from schemas.user import UserRead

logger = logging.getLogger(__name__)


class UserService:

    def __init__(
        self,
        db: AsyncSession,
        cacher: AbstractCache,
    ):
        self.db = db
        self.cacher = cacher

    async def get_profile(self, user_id: str) -> UserRead:
        stmt = select(User).where(User.id == user_id)
        user = await self.db.scalar(stmt)
        return user

    async def get_history(self, user_id: str) -> List[HistoryRead]:
        stmt = (
            select(SessionHistory)
            .where(
                and_(
                    SessionHistory.user_id == user_id,
                    SessionHistory.name.in_(
                        [
                            SessionHistoryChoices.LOGIN_WITH_PASSWORD,
                            SessionHistoryChoices.REFRESH_TOKEN_UPDATE,
                        ]
                    ),
                )
            )
            .order_by(SessionHistory.created_at)
        )
        result = await self.db.scalars(stmt)
        sess_hist = [HistoryRead.model_validate(row) for row in result]
        return sess_hist


def get_user_service(
    db: AsyncSession = Depends(get_db),
    cacher: AbstractCache = Depends(get_cacher),
) -> UserService:
    """
    Функция для создания экземпляра класса UserService
    """
    return UserService(db=db, cacher=cacher)

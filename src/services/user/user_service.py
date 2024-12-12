import logging
from typing import List

from fastapi import Depends

from db.casher import AbstractCache, get_cacher
from schemas.session import HistoryRead
from schemas.user import UserRead
from services.user import IUserRepository
from services.user.user_repository import get_repository

logger = logging.getLogger(__name__)


class UserService:

    def __init__(
        self,
        repository: IUserRepository,
        cacher: AbstractCache,
    ):
        self.repository = repository
        self.cacher = cacher

    async def get_profile(self, user_id: str) -> UserRead:
        """
        Получение данных о пользователе

        :param user_id: ID пользователя
        """
        user = await self.repository.get_profile(user_id)
        return user

    async def get_history(self, user_id: str) -> List[HistoryRead]:
        """
        Получение истории логинов пользователя

        :param user_id: ID пользователя
        """
        sess_hist = await self.repository.get_history(user_id)
        return sess_hist


def get_user_service(
    repository: IUserRepository = Depends(get_repository),
    cacher: AbstractCache = Depends(get_cacher),
) -> UserService:
    """
    Функция для создания экземпляра класса UserService
    """
    return UserService(repository=repository, cacher=cacher)

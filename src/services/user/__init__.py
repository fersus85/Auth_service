from abc import ABC, abstractmethod
from typing import List, Type

from schemas.session import HistoryRead
from schemas.user import UserRead


class IUserRepository(ABC):
    @abstractmethod
    async def get_profile(self, user_id: str) -> UserRead:
        """
        Получение данных о пользователе

        :param user_id: ID пользователя
        """
        pass

    @abstractmethod
    async def get_history(self, user_id: str) -> List[HistoryRead]:
        """
        Получение истории логинов пользователя

        :param user_id: ID пользователя
        """
        pass


user_repository_class: Type[IUserRepository] | None = None


async def get_user_repository_class() -> Type[IUserRepository]:
    return user_repository_class

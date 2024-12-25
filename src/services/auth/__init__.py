from abc import ABC, abstractmethod
from typing import Type
from uuid import UUID

from models import SessionHistoryChoices, User
from schemas.user import UserCreate, UserRead, UserRole
from schemas.yndx_oauth import UserInfoSchema


class IAuthRepository(ABC):
    @abstractmethod
    async def create_user(self, to_create: UserCreate) -> UserRead:
        """
        Создаёт нового пользователя с ролью юзер

        :param to_create: Схема на основе которой
            нужно создать нового пользователя
        """
        pass

    @abstractmethod
    async def update_user(
        self, user_db: User, user_info: UserInfoSchema
    ) -> UserRead:
        """
        Обновляет информацию о пользователе.

        :param user_db: Существующий пользователь из базы данных.
        :param user_info: Схема с новой информацией о пользователе.
        :return: Обновленная информация о пользователе.
        """
        pass

    @abstractmethod
    async def get_user_by_login(self, login: str) -> User:
        """
        Находит и возвращает пользователя по его логину.

        :param login: Логин пользователя
        """
        pass

    @abstractmethod
    async def get_user_with_roles_by_login(self, login: str) -> UserRole:
        """
        Получение данных о пользователе с ролями по логину
        """
        pass

    @abstractmethod
    async def check_refresh_token_in_active_session(
        self, user_id: UUID, user_agent: str, refresh_token: str
    ) -> bool:
        """
        Проверяет наличие refresh токена в списке активных сессий в БД

        :param user_id: ID пользователя
        :param user_agent: девайс пользователя
        :param refresh_token: закодированный токен
        """
        pass

    @abstractmethod
    async def insert_new_active_session(
        self, user_id: UUID, user_agent: str, refresh_token: str
    ) -> None:
        """
        Добавляет новую активную сессию с refresh токеном в БД

        :param user_id: ID пользователя
        :param user_agent: девайс пользователя
        :param refresh_token: закодированный токен
        """
        pass

    @abstractmethod
    async def delete_active_session(
        self, user_id: str, user_agent: str
    ) -> None:
        """
        Удаляет активную сессию заданного пользователя/девайса

        :param user_id: ID пользователя
        :param user_agent: девайс пользователя
        """
        pass

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass


auth_repository_class: Type[IAuthRepository] | None = None


async def get_auth_repository_class() -> Type[IAuthRepository]:
    return auth_repository_class

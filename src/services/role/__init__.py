from abc import ABC, abstractmethod
from typing import List, Type
from uuid import UUID

from schemas.role import RoleCreate, RoleFull, RoleUpdate


class IRoleRepository(ABC):
    @abstractmethod
    async def create(self, to_create: RoleCreate) -> RoleFull:
        """
        Создаёт новую роль

        :param to_create: Схема на основе которой нужно создать новую роль
        """
        pass

    @abstractmethod
    async def get(self, role_id: UUID) -> RoleFull:
        """
        Получает роль по её идентификатору
        """
        pass

    @abstractmethod
    async def get_by_name(self, name: str) -> RoleFull:
        """
        Получает роль по её названию
        """
        pass

    @abstractmethod
    async def update(self, role_id: UUID, to_update: RoleUpdate) -> RoleFull:
        """
        Обновляет имя/описание роли

        :param role_id: Уникальный идентификатор роли
        :param to_update: Схема на основе которой нужно обновить поля.
            Если поля имеют значение None, то их обновлять не нужно
        """
        pass

    @abstractmethod
    async def delete(self, role_id: UUID) -> None:
        """
        Удаляет роль по её идентификатору
        """
        pass

    @abstractmethod
    async def assign(self, role_id: UUID, user_id: UUID) -> None:
        """
        Назначает роль пользователю
        """
        pass

    @abstractmethod
    async def list_roles(
        self, name_filter: str | None = None
    ) -> List[RoleFull]:
        """
        Возвращает список ролей, с возможностью фильтрации по названию.

        :param name_filter: Строка для фильтрации ролей по названию,
            с символом подстановки '%' по необходимости.
            Если None, то вывести все существующие роли
        """
        pass


role_repository_class: Type[IRoleRepository] | None = None


async def get_role_repository_class() -> Type[IRoleRepository]:
    return role_repository_class

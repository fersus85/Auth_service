from typing import List
from uuid import UUID

from fastapi.params import Depends

from schemas.role import RoleCreate, RoleFull, RoleUpdate
from services.role import IRoleRepository
from services.role.role_repository import get_repository


class RoleService:
    """
    Сервис для управления ролями пользователей
    """

    def __init__(self, repository: IRoleRepository):
        self.repository = repository

    async def create(self, to_create: RoleCreate) -> RoleFull:
        """
        Создаёт новую роль

        :param to_create: Схема на основе которой нужно создать новую роль

        :raise RoleServiceExc: Если роль с таким name уже существует
        """

        created_role = await self.repository.create(to_create)

        return RoleFull.model_validate(created_role)

    async def get(self, role_id: UUID) -> RoleFull | None:
        """
        Получает роль по её идентификатору
        """

        return await self.repository.get(role_id)

    async def get_by_name(self, name: str) -> RoleFull | None:
        """
        Получает роль по её названию
        """

        return await self.repository.get_by_name(name)

    async def update(
        self, role_id: UUID, to_update: RoleUpdate
    ) -> RoleFull | None:
        """
        Обновляет имя/описание роли

        :param role_id: Уникальный идентификатор роли
        :param to_update: Схема на основе которой нужно обновить поля.
            Если поля имеют значение None, то их обновлять не нужно
        """

        return await self.repository.update(role_id, to_update)

    async def delete(self, role_id: UUID) -> None:
        """
        Удаляет роль по её идентификатору

        :raise RoleServiceExc: Если не удалось удалить роль
        """

        await self.repository.delete(role_id)

    async def assign(self, role_id: UUID, user_id: UUID) -> None:
        """
        Назначает роль пользователю

        :raise RoleServiceExc: Если не удалось привязать роль к пользователю
        """

        await self.repository.assign(role_id, user_id)

    async def list_roles(
        self, name_filter: str | None = None
    ) -> List[RoleFull]:
        """
        Возвращает список ролей, с возможностью фильтрации по названию.

        :param name_filter: Строка для фильтрации ролей по названию,
            с символом подстановки '%' по необходимости.
            Если None, то вывести все существующие роли
        """

        return await self.repository.list_roles(name_filter)


def get_role_service(
    repository: IRoleRepository = Depends(get_repository),
) -> RoleService:
    """
    Функция для создания экземпляра класса RoleService
    """
    return RoleService(repository=repository)

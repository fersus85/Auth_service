from contextlib import asynccontextmanager
from typing import Any, List, Type
from uuid import UUID

from fastapi import Depends
from sqlalchemy import delete, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import UserRoleDefault
from models import Role
from models.user import user_roles
from schemas.role import RoleCreate, RoleFull, RoleUpdate
from services import get_data_access
from services.role import (
    IRoleRepository,
    NoResult,
    RoleServiceExc,
    get_role_repository_class,
)


class SQLAlchemyRoleRepository(IRoleRepository):
    def __init__(self, db_session: AsyncSession):
        """
        Инициализация сервиса ролей сессией SQLAlchemy,
        связанной с таблицей roles
        """
        self.db_session = db_session

    async def create(self, to_create: RoleCreate) -> RoleFull:
        """
        Создаёт новую роль

        :param to_create: Схема на основе которой нужно создать новую роль
        """

        role = Role(**to_create.model_dump())
        async with self._transaction_handler("Can't create new role"):
            self.db_session.add(role)

        return RoleFull.model_validate(role)

    async def get(self, role_id: UUID) -> RoleFull | None:
        """
        Получает роль по её идентификатору
        """
        stmt = select(Role).where(Role.id == role_id)
        role = await self.db_session.scalar(stmt)

        return role and RoleFull.model_validate(role)

    async def get_by_name(self, name: str) -> RoleFull | None:
        """
        Получает роль по её названию
        """
        stmt = select(Role).where(Role.name == name)
        role = await self.db_session.scalar(stmt)

        return role and RoleFull.model_validate(role)

    async def update(
        self, role_id: UUID, to_update: RoleUpdate
    ) -> RoleFull | None:
        """
        Обновляет имя/описание роли

        :param role_id: Уникальный идентификатор роли
        :param to_update: Схема на основе которой нужно обновить поля.
            Если поля имеют значение None, то их обновлять не нужно
        """

        update_data = {**to_update.model_dump(exclude_unset=True)}
        if not update_data:
            raise RoleServiceExc("No fields to update")

        stmt = (
            update(Role)
            .returning(Role)
            .where(Role.id == role_id)
            .values(update_data)
        )
        async with self._transaction_handler("Can't update role"):
            role = await self.db_session.scalar(stmt)

        return role and RoleFull.model_validate(role)

    async def delete(self, role_id: UUID) -> None:
        """
        Удаляет роль по её идентификатору
        """
        stmt = delete(Role).where(Role.id == role_id)
        async with self._transaction_handler("Can't delete role"):
            result = await self.db_session.execute(stmt)
            if result.rowcount == 0:
                raise NoResult(f"No role with id {role_id} found")

    async def assign(self, role_id: UUID, user_id: UUID) -> None:
        """
        Назначает роль пользователю
        """
        stmt = (
            update(user_roles)
            .where(user_roles.c.user_id == user_id)
            .values(role_id=role_id)
        )
        async with self._transaction_handler("Can't assign role"):
            await self.db_session.execute(stmt)

    async def revoke(self, user_id: UUID) -> None:
        """
        Отзывает роль у пользователя

        :raise RoleServiceExc: Если не удалось отозвать роль у пользователя
        """
        role_stmt = select(Role).where(Role.name == UserRoleDefault.USER)
        role = await self.db_session.scalar(role_stmt)
        stmt = (
            update(user_roles)
            .where(user_roles.c.user_id == user_id)
            .values(role_id=role.id)
        )

        async with self._transaction_handler("Can't revoke role"):
            await self.db_session.execute(stmt)

    async def list_roles(
        self, name_filter: str | None = None
    ) -> List[RoleFull]:
        """
        Возвращает список ролей, с возможностью фильтрации по названию.

        :param name_filter: Строка для фильтрации ролей по названию,
            с символом подстановки '%' по необходимости.
            Если None, то вывести все существующие роли
        """
        if name_filter is None:
            stmt = select(Role)
        else:
            stmt = select(Role).where(Role.name.like(name_filter))

        roles = await self.db_session.scalars(stmt)

        return [RoleFull.model_validate(row) for row in roles.fetchmany()]

    @asynccontextmanager
    async def _transaction_handler(self, error_message: str):
        try:
            yield
            await self.db_session.commit()
        except IntegrityError as e:
            await self.db_session.rollback()
            raise RoleServiceExc(error_message) from e


async def get_repository(
    data_access: Any = Depends(get_data_access),
    role_repository_class: Type[IRoleRepository] = Depends(
        get_role_repository_class
    ),
) -> IRoleRepository:
    return role_repository_class(data_access)

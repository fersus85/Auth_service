import logging

from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncSession

from models import ActiveSession, Role

__all__ = ("Role", "ActiveSession")

logger = logging.getLogger(__name__)


async def insert_roles(session: AsyncSession, roles: list[Role]):
    """
    Записывает в базу данных дефолтные роли

    :param session: Асинхронная сессия подключения к бд
    :param roles: Список с дефолтными ролями
    """
    role_mappings = [
        {"name": role.name, "description": role.description} for role in roles
    ]
    logger.info("Inserting roles...")
    await session.execute(insert(Role), role_mappings)
    await session.commit()

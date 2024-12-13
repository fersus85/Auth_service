import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from db.postrges_db import psql
from init_services import (
    init_casher,
    init_postgresql_service,
    init_repositories,
)
from models.user import Role
from scripts.create_default_roles import insert_roles

logger = logging.getLogger(__name__)

DEFAULT_ROLES = [
    Role(name="superuser", description="Может всё"),
    Role(name="admin", description="Администратор"),
    Role(name="subscriber", description="Пользователь с допами"),
    Role(name="user", description="Зарегестрированный пользователь"),
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_postgresql_service()
    await init_repositories()
    await init_casher()

    async for session in psql.get_db():
        await insert_roles(session, DEFAULT_ROLES)

    logger.debug("Successfully connected")
    yield
    await psql.psql_sevice.dispose()
    logger.debug("Closing connections")

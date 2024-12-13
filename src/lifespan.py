import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from redis.asyncio import Redis

import db.casher as cacher
from core.config import settings
from db import redis
from db.postrges_db import psql
from db.redis import RedisCache
from init_services import init_postgresql_service, init_repositories
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
    redis.redis = Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT)
    cacher.cacher = RedisCache(redis.redis)

    async for session in psql.get_db():
        await insert_roles(session, DEFAULT_ROLES)

    logger.debug("Successfully connected")
    yield
    await psql.psql_sevice.dispose()
    logger.debug("Closing connections")

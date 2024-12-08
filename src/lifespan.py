import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from redis.asyncio import Redis

import db.casher as cacher
import services as service
from core.config import settings
from db import redis
from db.postrges_db import psql
from db.postrges_db.psql import PostgresService, get_db
from db.redis import RedisCache
from services.role.role_repository import SQLAlchemyRoleRepository
from services.auth.auth_repository import SQLAlchemyAuthRepository

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    psql.psql = PostgresService(
        url=str(settings.DB_URI),
        echo=settings.ECHO,
        echo_pool=settings.ECHO_POOL,
        pool_size=settings.POOL_SIZE,
        max_overflow=settings.MAX_OVERFLOW,
    )
    redis.redis = Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT)
    cacher.cacher = RedisCache(redis.redis)

    service.data_access_factory = get_db
    service.role.role_repository_class = SQLAlchemyRoleRepository
    service.auth.auth_repository_class = SQLAlchemyAuthRepository

    logger.debug("Successfully connected")
    yield
    await psql.psql.dispose()
    logger.debug("Closing connections")

from redis.asyncio import Redis

import db.casher as cacher
import services
from core.config import settings
from db import redis
from db.postrges_db import psql
from db.postrges_db.psql import PostgresService
from services.auth.auth_repository import SQLAlchemyAuthRepository
from services.role.role_repository import SQLAlchemyRoleRepository
from services.user.user_repository import SQLAlchemyUserRepository


async def init_postgresql_service():
    psql.psql_service = PostgresService(
        url=str(settings.DB_URI),
        echo=settings.ECHO,
        echo_pool=settings.ECHO_POOL,
        pool_size=settings.POOL_SIZE,
        max_overflow=settings.MAX_OVERFLOW,
    )


async def init_repositories():
    services.data_access_factory = psql.get_db
    services.role.role_repository_class = SQLAlchemyRoleRepository
    services.auth.auth_repository_class = SQLAlchemyAuthRepository
    services.user.user_repository_class = SQLAlchemyUserRepository


async def init_casher():
    redis.redis = Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT)
    cacher.cacher = redis.RedisCache(redis.redis)

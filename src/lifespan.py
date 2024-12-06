import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from core.config import settings
from db.postrges_db import psql
from db.postrges_db.psql import PostgresService

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
    logger.debug("Successfully connected")
    yield
    await psql.psql.dispose()
    logger.debug("Closing connections")

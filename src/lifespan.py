import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from db.postrges_db.psql import psql_service
from init_services import (
    init_casher,
    init_postgresql_service,
    init_repositories,
    insert_default_roles,
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Иницилизирует сервисы перед стартом
    приложения и зыкрывает соединения после
    """
    await init_postgresql_service()
    await init_repositories()
    await init_casher()
    await insert_default_roles()

    logger.info("App ready")
    yield
    await psql_service.dispose()
    logger.debug("Closing connections")

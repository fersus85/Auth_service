from typing import AsyncGenerator, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from db.postrges_db.psql import PostgresService

psql_sevice: Optional[PostgresService] = None


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Предоставляет объект AsyncSession."""
    async for session in psql_sevice.session_getter():
        yield session


async def init_postgresql_service():
    global psql_sevice
    psql_sevice = PostgresService(
        url=str(settings.DB_URI),
        echo=settings.ECHO,
        echo_pool=settings.ECHO_POOL,
        pool_size=settings.POOL_SIZE,
        max_overflow=settings.MAX_OVERFLOW,
    )

from typing import AsyncGenerator, Optional

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


class PostgresService:
    def __init__(
        self,
        url: str,
        echo: bool = False,
        echo_pool: bool = False,
        pool_size: int = 5,
        max_overflow: int = 10,
    ) -> None:
        self.engine: AsyncEngine = create_async_engine(
            url=url,
            echo=echo,
            echo_pool=echo_pool,
            pool_size=pool_size,
            max_overflow=max_overflow,
        )
        self.session_factory = async_sessionmaker(
            bind=self.engine,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
        )

    async def dispose(self) -> None:
        """
        Асинхронный метод для корректного завершения
        работы движка базы данных, освобождая все ресурсы.
        """
        await self.engine.dispose()

    async def session_getter(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Асинхронный генератор, который создает новую сессию при каждом вызове
        и автоматически закрывает её после использования.
        """
        async with self.session_factory() as session:
            yield session


psql: Optional[PostgresService] = None


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Предоставляет объект AsyncSession."""
    async for session in psql.session_getter():
        yield session

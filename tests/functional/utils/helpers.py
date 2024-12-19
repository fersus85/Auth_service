from enum import Enum
from uuid import UUID

from settings import test_settings
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.security import generate_password_hash

from cli.su_management import async_launcher
from db.postrges_db.psql import PostgresService
from models.user import Role, User


class RequestMethods(Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"


async def init_postgresql_service():
    """Возвращает новый экземпляр PostgresService"""
    return PostgresService(
        url=str(test_settings.DB_URI),
        echo=test_settings.ECHO,
        echo_pool=test_settings.ECHO_POOL,
        pool_size=test_settings.POOL_SIZE,
        max_overflow=test_settings.MAX_OVERFLOW,
    )


@async_launcher
async def init_roles():
    psql = await init_postgresql_service()
    async for session in psql.session_getter():
        try:
            role = Role(
                id=UUID("bef8c6fd-989b-4bb3-848a-89414eadc38f"),
                name="test",
                description="test role",
            )
            session.add(role)
            await session.commit()
        except SQLAlchemyError:
            session.rollback()


@async_launcher
async def init_users():
    psql = await init_postgresql_service()
    async for session in psql.session_getter():
        try:
            result = await session.execute(
                select(Role).where(
                    Role.id == UUID("42966562-ec42-44a0-afd6-e72d1a839256")
                )
            )
            role = result.scalars().first()

            user = User(
                id=UUID("afa6b9a3-5db1-4c44-b467-137394c2b167"),
                login=test_settings.TEST_USER_LOGIN,
                password_hash=generate_password_hash(
                    test_settings.TEST_USER_PASSWORD
                ),
                roles=[role],
            )

            session.add(user)
            await session.commit()
        except SQLAlchemyError:
            session.rollback()

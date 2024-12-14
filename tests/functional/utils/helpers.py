from enum import Enum
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.security import generate_password_hash

from cli.su_management import async_launcher, init_postgresql_service
from models.user import Role, User
from tests.functional.settings import test_settings


class RequestMethods(Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"


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

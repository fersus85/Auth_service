import asyncio
from functools import wraps

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from werkzeug.security import generate_password_hash

from core.config import settings
from db.postrges_db.psql import PostgresService
from models.user import Role, User
from schemas.user import UserCreate


def async_launcher(func):
    """Обёртка для запуска в Typer async funcs"""

    @wraps(func)
    def wrapper(*args, **kwargs):
        return asyncio.run(func(*args, **kwargs))

    return wrapper


async def init_postgresql_service():
    """Возвращает новый экземпляр PostgresService"""
    return PostgresService(
        url=str(settings.DB_URI),
        echo=settings.ECHO,
        echo_pool=settings.ECHO_POOL,
        pool_size=settings.POOL_SIZE,
        max_overflow=settings.MAX_OVERFLOW,
    )


class UserAlreadyExistsError(Exception):
    def __init__(self, login):
        super().__init__(f"Login: '{login}' is already taken another user")
        self.login = login


async def insert_superuser(session: AsyncSession, creds: UserCreate) -> User:
    """
    Создает нового супер пользователя с указанным логином и паролем.

    В случае неудачи выбрасывает
    исключение UserAlreadyExistsError.

    Args:
        session (AsyncSession): Асинхронная сессия базы данных.
        creds (UserCreate): пароль и логин

    Raises:
        UserAlreadyExistsError: Если не удалось создаьть запись
    """
    ROLE: str = "superuser"
    user_create_dict = creds.model_dump()

    password = user_create_dict.pop("password")
    user_create_dict["password_hash"] = generate_password_hash(password)
    new_su = User(**user_create_dict)

    stmt = select(Role).where(Role.name == ROLE)
    role_instance = await session.scalar(stmt)
    new_su.roles.append(role_instance)
    try:
        session.add(new_su)
        await session.commit()
    except IntegrityError as e:
        await session.rollback()
        raise UserAlreadyExistsError(creds.login) from e

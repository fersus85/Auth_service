from sqlalchemy import insert, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from werkzeug.security import generate_password_hash

from models.user import Role, User


async def create_user(
    session: AsyncSession, login: str, password: str
) -> User:
    """
    Создает нового пользователя с указанным логином и паролем.

    Проверяет, существует ли пользователь с данным логином.
    Если пользователь уже существует, выбрасывает исключение ValueError.

    Args:
        session (AsyncSession): Асинхронная сессия базы данных.
        login (str): Логин нового пользователя.
        password (str): Пароль нового пользователя.

    Returns:
        User: Созданный объект пользователя.

    Raises:
        ValueError: Если пользователь с данным логином уже существует.
    """
    new_user = User(
        login=login, password_hash=generate_password_hash(password)
    )
    session.add(new_user)
    try:
        await session.commit()
        return new_user
    except IntegrityError as e:
        await session.rollback()
        raise ValueError("User %s already exists.", login) from e


async def assign_role(
    session: AsyncSession, user: User, role_name: str
) -> None:
    """
    Назначает указанную роль пользователю.

    Проверяет, существует ли роль с данным именем.
    Если роль не найдена, выбрасывает исключение ValueError.

    Args:
        session (AsyncSession): Асинхронная сессия базы данных.
        user (User): Объект пользователя, которому будет назначена роль.
        role_name (str): Имя роли, которую нужно назначить.

    Raises:
        ValueError: Если роль с данным именем не найдена.
    """
    stmt = select(Role).where(Role.name == role_name)
    role_instance = await session.scalar(stmt)

    if not role_instance:
        raise ValueError("Роль '%s' не найдена.", role_name)
    try:
        stmt = insert(User.roles).values(
            role_id=role_instance.id, user_id=user.id
        )
        await session.execute(stmt)
        await session.commit()
    except IntegrityError as e:
        await session.rollback()
        raise ValueError("IntegrityError") from e

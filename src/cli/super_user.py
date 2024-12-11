import logging

import typer

from cli.su_management import assign_role, create_user
from services import get_data_access

app = typer.Typer()
logger = logging.getLogger(__name__)


@app.command()
async def create_superuser(login: str, password: str) -> None:
    """
    Создает суперпользователя с указанным логином и паролем.

    Вызывает функции для создания пользователя и назначения ему "superuser".
    Обрабатывает возможные ошибки и выводит соответствующие сообщения.

    Args:
        login (str): Логин суперпользователя.
        password (str): Пароль суперпользователя.
    """
    async with get_data_access() as session:
        try:
            new_user = await create_user(session, login, password)
            await assign_role(session, new_user, "superuser")
            typer.echo(f"Суперпользователь {login} успешно создан.")
            logger.info("Суперпользователь %s успешно создан.", login)
        except ValueError as e:
            typer.echo(str(e))


if __name__ == "__main__":
    app()

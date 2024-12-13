import logging

import typer
from su_management import (
    UserAlreadyExistsError,
    async_launcher,
    init_postgresql_service,
    insert_superuser,
)

from schemas.user import UserCreate

app = typer.Typer()
logger = logging.getLogger(__name__)


@app.command()
@async_launcher
async def createsuperuser(
    login: str = typer.Option(..., prompt=True),
    password: str = typer.Option(
        ...,
        prompt=True,
        hide_input=True,
        confirmation_prompt="Confirm password: ",
    ),
) -> None:
    """
    Создает суперпользователя с указанным логином и паролем.

    Вызывает функцию для создания пользователя с  "superuser".
    Обрабатывает возможные ошибки и выводит соответствующие сообщения.

    Args:
        login (str): Логин суперпользователя.
        password (str): Пароль суперпользователя.
    """
    credentials = UserCreate(login=login, password=password)
    psql = await init_postgresql_service()
    try:
        async for session in psql.session_getter():
            await insert_superuser(session=session, creds=credentials)
            typer.secho("Superuser successfuly created", fg=typer.colors.GREEN)
            logger.info("Superuser created...")
    except UserAlreadyExistsError as e:
        typer.secho(str(e), fg=typer.colors.RED)
        logger.error("Failed to create superuser %s: %s", login, e)
    except Exception as e:
        typer.secho(f"An unexpected error occurred: {e}", fg=typer.colors.RED)
        logger.exception(
            "Failed to create superuser %s due to an unexpected error:",
            login,
        )


if __name__ == "__main__":
    app()

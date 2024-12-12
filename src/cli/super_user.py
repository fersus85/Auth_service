import logging

import typer

from cli.su_management import (
    RolesNotAssignedError,
    UserAlreadyExistsError,
    assign_role,
    create_user,
)
from models.user import User
from services import get_data_access

app = typer.Typer()
logger = logging.getLogger(__name__)


@app.command()
async def create_superuser(
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

    Вызывает функции для создания пользователя и назначения ему "superuser".
    Обрабатывает возможные ошибки и выводит соответствующие сообщения.

    Args:
        login (str): Логин суперпользователя.
        password (str): Пароль суперпользователя.
    """
    async with get_data_access() as session:
        try:
            new_user: User = await create_user(session, login, password)

            await assign_role(session, new_user, "superuser")

            typer.secho(
                f"Суперпользователь {login} успешно создан.",
                fg=typer.colors.GREEN,
            )
            logger.info("Суперпользователь %s успешно создан.", login)

        except UserAlreadyExistsError as e:
            typer.secho(str(e), fg=typer.colors.RED)
            logger.error("Failed to create superuser %s: %s", login, e)
        except RolesNotAssignedError as e:
            typer.secho(str(e), fg=typer.colors.RED)
            logger.error("Failed to create superuser %s: %s", login, e)
        except Exception as e:
            typer.secho(
                f"An unexpected error occurred: {e}", fg=typer.colors.RED
            )
            logger.exception(
                "Failed to create superuser %s due to an unexpected error:",
                login,
            )


if __name__ == "__main__":
    app()

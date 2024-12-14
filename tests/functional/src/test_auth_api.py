from http import HTTPStatus
from typing import Any, Callable, Dict

import pytest
from aiohttp import ClientResponse


@pytest.mark.parametrize(
    "post_body, exp_status, exp_result",
    [
        pytest.param(
            {
                "login": "terminator1",
                "first_name": "Ivan",
                "last_name": "Petrov",
                "password": "Qwerty123",
            },
            HTTPStatus.CREATED,
            None,
            id="create new user",
        ),
        pytest.param(
            {
                "login": "terminator1",
                "first_name": "Ivan",
                "last_name": "Petrov",
                "password": "Qwerty123",
            },
            HTTPStatus.CONFLICT,
            "Record already exists",
            id="create the same user",
        ),
        pytest.param(
            {
                "login": "terminator2",
                "first_name": "Ivan",
                "last_name": "Petrov",
                "password": "123",
            },
            HTTPStatus.BAD_REQUEST,
            "Password length must > 7 and login length > 3",
            id="create user with short password",
        ),
    ],
)
@pytest.mark.asyncio
async def test_signup(
    make_post_request: Callable[[str, str, Dict[str, Any]], ClientResponse],
    post_body: Dict[str, Any],
    exp_status: HTTPStatus,
    exp_result: str | None,
) -> None:
    """
    Тест регистрации пользователя.
    Проверяем регистрацию с достаточно длинным паролем,
    со слишком коротким паролем
    и попытку регистрации существующего пользователя.
    """
    response = await make_post_request("/auth/signup", "", post_body)

    body = await response.json()

    assert response.status == exp_status

    if exp_status == HTTPStatus.CREATED:
        assert "id" in body
        assert "created_at" in body
        assert body.get("first_name") == post_body.get("first_name")
        assert body.get("last_name") == post_body.get("last_name", "")
    else:
        assert body.get("detail") == exp_result


@pytest.mark.parametrize(
    "post_body, exp_status, exp_result",
    [
        pytest.param(
            {"login": "invalid", "password": "Qwerty123"},
            HTTPStatus.UNAUTHORIZED,
            "Invalid login or password",
            id="login with invalid user",
        ),
        pytest.param(
            {"login": "terminator1", "password": "invalid"},
            HTTPStatus.UNAUTHORIZED,
            "Invalid login or password",
            id="login with invalid password",
        ),
        pytest.param(
            {"login": "terminator1", "password": "Qwerty123"},
            HTTPStatus.OK,
            None,
            id="login correctly",
        ),
    ],
)
@pytest.mark.asyncio
async def test_login(
    make_post_request: Callable[[str, str, Dict[str, Any]], ClientResponse],
    post_body: Dict[str, Any],
    exp_status: HTTPStatus,
    exp_result: str | None,
) -> None:
    """
    Тестирование входа пользователя.
    Выполняем попытку входа несуществующего пользователя,
    с неверным паролем, с корректными данными.
    """
    response: ClientResponse = await make_post_request(
        "/auth/login", "", post_body
    )

    body = await response.json()

    assert response.status == exp_status

    if exp_status == HTTPStatus.CREATED:
        assert "access_token" in body
        assert "refresh_token" in body
        assert body.get("first_name") == post_body.get("first_name")
        assert body.get("last_name") == post_body.get("last_name", "")
    else:
        assert body.get("detail") == exp_result


@pytest.mark.asyncio
async def test_profile(
    make_get_request: Callable[[str, str, str], ClientResponse],
) -> None:
    """
    Проверка чтения своего профиля.
    """
    response: ClientResponse = await make_get_request("/profile", "", "")

    body = await response.json()

    assert response.status == HTTPStatus.OK

    assert "id" in body
    assert "login" in body
    assert "first_name" in body
    assert "last_name" in body


@pytest.mark.asyncio
async def test_profile_history(
    make_get_request: Callable[[str, str, str], ClientResponse],
) -> None:
    """
    Проверка чтения своей истории входов,
    в которой сейчас должен быть только один вход.
    """
    response: ClientResponse = await make_get_request(
        "/profile/history", "", ""
    )

    body = await response.json()

    assert response.status == HTTPStatus.OK

    assert len(body) == 1


@pytest.mark.asyncio
async def test_refresh(
    make_post_request: Callable[[str, str, Dict[str, Any]], ClientResponse],
) -> None:
    """
    Проверка обновления токенов доступа.
    """
    response: ClientResponse = await make_post_request(
        "/auth/token/refresh", "", ""
    )

    body = await response.json()

    assert response.status == HTTPStatus.OK
    assert "access_token" in body
    assert "refresh_token" in body


@pytest.mark.parametrize(
    "post_body, exp_status, exp_result",
    [
        pytest.param(
            {"password": "qwe"},
            HTTPStatus.BAD_REQUEST,
            "Password length must > 7 and login length > 3",
            id="short password",
        ),
        pytest.param(
            {"password": "QwertyNewPass"},
            HTTPStatus.OK,
            None,
            id="new password",
        ),
    ],
)
@pytest.mark.asyncio
async def test_password_update(
    make_post_request: Callable[[str, str, Dict[str, Any]], ClientResponse],
    post_body: Dict[str, Any],
    exp_status: HTTPStatus,
    exp_result: str | None,
) -> None:
    """
    Проверка смены пароля.
    """
    response: ClientResponse = await make_post_request(
        "/auth/password_update", "", post_body
    )

    body = await response.json()

    assert response.status == exp_status

    if exp_status == HTTPStatus.BAD_REQUEST:
        assert body.get("detail") == exp_result


@pytest.mark.parametrize(
    "post_body, exp_status, exp_result",
    [
        pytest.param(
            None,
            HTTPStatus.NO_CONTENT,
            None,
            id="logout",
        ),
        pytest.param(
            None,
            HTTPStatus.UNAUTHORIZED,
            "Access token not found",
            id="second logout",
        ),
    ],
)
@pytest.mark.asyncio
async def test_logout(
    make_post_request: Callable[[str, str, Dict[str, Any]], ClientResponse],
    post_body: Dict[str, Any],
    exp_status: HTTPStatus,
    exp_result: str | None,
) -> None:
    """
    Проверка выхода пользователя.
    При повтороной попытке возвращает ошибку.
    """
    response: ClientResponse = await make_post_request(
        "/auth/logout", "", post_body
    )

    body = await response.json()

    assert response.status == exp_status

    if response.status == HTTPStatus.UNAUTHORIZED:
        assert body.get("detail") == exp_result


@pytest.mark.parametrize(
    "post_body, exp_status, exp_result",
    [
        pytest.param(
            {"login": "terminator1", "password": "Qwerty123"},
            HTTPStatus.UNAUTHORIZED,
            "Invalid login or password",
            id="login with old password",
        ),
        pytest.param(
            {"login": "terminator1", "password": "QwertyNewPass"},
            HTTPStatus.OK,
            None,
            id="login with new password",
        ),
    ],
)
@pytest.mark.asyncio
async def test_login_new_password(
    make_post_request: Callable[[str, str, Dict[str, Any]], ClientResponse],
    post_body: Dict[str, Any],
    exp_status: HTTPStatus,
    exp_result: str | None,
) -> None:
    """
    Проверка входа пользователя со старым и новым паролем.
    """
    response: ClientResponse = await make_post_request(
        "/auth/login", "", post_body
    )
    body = await response.json()

    assert response.status == exp_status

    if exp_status == HTTPStatus.CREATED:
        assert "access_token" in body
        assert "refresh_token" in body
        assert body.get("first_name") == post_body.get("first_name")
        assert body.get("last_name") == post_body.get("last_name", "")
    else:
        assert body.get("detail") == exp_result


@pytest.mark.asyncio
async def test_profile_history_again(
    make_get_request: Callable[[str, str, str], ClientResponse],
) -> None:
    """
    Проверка истории входов, в которой теперь должно быть два события.
    """
    response: ClientResponse = await make_get_request(
        "/profile/history", "", ""
    )

    body = await response.json()

    assert response.status == HTTPStatus.OK
    assert len(body) == 2

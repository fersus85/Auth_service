from http import HTTPStatus
from typing import Any, Callable, Dict, List

import pytest
from aiohttp import ClientResponse
from utils.helpers import RequestMethods


@pytest.mark.parametrize(
    "role_id, exp_result",
    [
        pytest.param(
            "42966562-ec42-44a0-afd6-e72d1a839256",
            {"status": HTTPStatus.OK, "name": "superuser"},
            id="success role get",
        ),
        pytest.param(
            "11111111-04c8-7b96-8037-1b5c65a5428a",
            {"status": HTTPStatus.NOT_FOUND, "name": None},
            id="not found role",
        ),
        pytest.param(
            "123",
            {"status": HTTPStatus.UNPROCESSABLE_ENTITY, "name": None},
            id="invalid input",
        ),
    ],
)
@pytest.mark.asyncio
async def test_role_info(
    make_request: Callable[
        [RequestMethods, str, str, str, Any], ClientResponse
    ],
    role_id: str,
    exp_result: Dict[str, Any],
) -> None:
    response = await make_request(RequestMethods.GET, "/role", "", role_id)
    body = await response.json()

    assert response.status == exp_result["status"]
    if exp_result["name"] is None:
        return

    assert body.get("id") == role_id
    assert body.get("name") == exp_result["name"]


@pytest.mark.parametrize(
    "query, exp_status, exp_result",
    [
        pytest.param(
            None,
            HTTPStatus.OK,
            [
                {
                    "id": "42966562-ec42-44a0-afd6-e72d1a839256",
                    "name": "superuser",
                    "description": "Может всё",
                },
                {
                    "id": "20afcc37-e8dc-473a-a3ce-a61e6b3d563e",
                    "name": "admin",
                    "description": "Администратор",
                },
                {
                    "id": "41987fd3-88cb-412c-9085-89201470610e",
                    "name": "subscriber",
                    "description": "Пользователь с допами",
                },
                {
                    "id": "ab1d025b-0e33-42e2-bba8-cf7125044263",
                    "name": "user",
                    "description": "Зарегестрированный пользователь",
                },
            ],
            id="all roles no query",
        ),
        pytest.param(
            "%er",
            HTTPStatus.OK,
            [
                {
                    "id": "42966562-ec42-44a0-afd6-e72d1a839256",
                    "name": "superuser",
                    "description": "Может всё",
                },
                {
                    "id": "41987fd3-88cb-412c-9085-89201470610e",
                    "name": "subscriber",
                    "description": "Пользователь с допами",
                },
                {
                    "id": "ab1d025b-0e33-42e2-bba8-cf7125044263",
                    "name": "user",
                    "description": "Зарегестрированный пользователь",
                },
            ],
            id="filter by '%er' query",
        ),
        pytest.param(
            "editor",
            HTTPStatus.OK,
            [
                {
                    "id": "94e94bc3-a29d-4149-857c-2bd1e141f0a3",
                    "name": "editor",
                    "description": "editor",
                },
            ],
            id="filter by 'editor' query",
        ),
        pytest.param(
            "nonexistent", HTTPStatus.OK, [], id="no roles match query"
        ),
    ],
)
@pytest.mark.asyncio
async def test_list_roles(
    make_request: Callable[
        [RequestMethods, str, str, str, Any], ClientResponse
    ],
    query: str | None,
    exp_status: HTTPStatus,
    exp_result: List[Dict[str, Any]],
) -> None:
    query_str = f"?query={query}" if query else ""
    response = await make_request(
        RequestMethods.GET, "/role", "/list", query_str
    )
    body = await response.json()

    assert response.status == exp_status

    for expected_role, returned_role in zip(exp_result, body):
        assert returned_role.get("id") == expected_role["id"]
        assert returned_role.get("name") == expected_role["name"]
        assert returned_role.get("description") == expected_role["description"]


@pytest.mark.parametrize(
    "body, exp_status, exp_result",
    [
        pytest.param(
            {"name": "test0", "description": "test_descr"},
            HTTPStatus.CREATED,
            None,
            id="create new role",
        ),
        pytest.param(
            {"name": "test1"},
            HTTPStatus.CREATED,
            None,
            id="create new role without description",
        ),
        pytest.param(
            {"name": "admin"},
            HTTPStatus.BAD_REQUEST,
            "Can't create new role",
            id="duplicate role creation",
        ),
    ],
)
@pytest.mark.asyncio
async def test_create_role(
    make_request: Callable[
        [RequestMethods, str, str, str, Any], ClientResponse
    ],
    body: Dict[str, Any],
    exp_status: HTTPStatus,
    exp_result: str | None,
) -> None:
    response = await make_request(RequestMethods.POST, "/role", "", "", body)
    body = await response.json()

    assert response.status == exp_status

    if exp_status == HTTPStatus.CREATED:
        assert "id" in body
        assert body.get("name") == body.get("name")
        assert body.get("description") == body.get("description", "")
    else:
        assert body.get("detail") == exp_result


@pytest.mark.parametrize(
    "role_id, post_body, exp_status, exp_result",
    [
        pytest.param(
            "bef8c6fd-989b-4bb3-848a-89414eadc38f",
            {"name": "test", "description": "test_upd1"},
            HTTPStatus.OK,
            None,
            id="update full",
        ),
        pytest.param(
            "bef8c6fd-989b-4bb3-848a-89414eadc38f",
            {"description": "test_upd2"},
            HTTPStatus.OK,
            None,
            id="update partial",
        ),
        pytest.param(
            "11111111-b076-4cda-8851-aa056e96725f",
            {"name": "administrator"},
            HTTPStatus.NOT_FOUND,
            "Role not found",
            id="update non-exist role",
        ),
        pytest.param(
            "bef8c6fd-989b-4bb3-848a-89414eadc38f",
            {"incorrect": "test_upd"},
            HTTPStatus.BAD_REQUEST,
            "No fields to update",
            id="incorrect update fields",
        ),
    ],
)
@pytest.mark.asyncio
async def test_update_role(
    make_request: Callable[
        [RequestMethods, str, str, str, Any], ClientResponse
    ],
    role_id: str,
    post_body: Dict[str, Any],
    exp_status: HTTPStatus,
    exp_result: str | None,
) -> None:
    response = await make_request(
        RequestMethods.PUT, "/role", "", role_id, post_body
    )
    body = await response.json()

    assert response.status == exp_status

    if exp_status != HTTPStatus.OK:
        assert body.get("detail") == exp_result


@pytest.mark.parametrize(
    "role_id, user_id, exp_status, exp_result",
    [
        pytest.param(
            "ab1d025b-0e33-42e2-bba8-cf7125044263",
            "afa6b9a3-5db1-4c44-b467-137394c2b167",
            HTTPStatus.NO_CONTENT,
            None,
            id="correct assign",
        ),
        pytest.param(
            "11111111-b076-4cda-8851-aa056e96725f",
            "afa6b9a3-5db1-4c44-b467-137394c2b167",
            HTTPStatus.BAD_REQUEST,
            "Can't assign role",
            id="non-exist role",
        ),
        pytest.param(
            "ab1d025b-0e33-42e2-bba8-cf7125044263",
            "11111111-b076-4cda-8851-aa056e96725f",
            HTTPStatus.BAD_REQUEST,
            "Can't assign role",
            id="non-exist user",
        ),
    ],
)
@pytest.mark.asyncio
async def test_assign_role(
    make_request: Callable[
        [RequestMethods, str, str, str, Any], ClientResponse
    ],
    role_id: str,
    user_id: str,
    exp_status: HTTPStatus,
    exp_result: str | None,
) -> None:
    response = await make_request(
        RequestMethods.POST,
        "/role",
        "/assign",
        "",
        {"role_id": role_id, "user_id": user_id},
    )
    body = await response.json()

    assert response.status == exp_status

    if exp_status != HTTPStatus.NO_CONTENT:
        assert body.get("detail") == exp_result


@pytest.mark.parametrize(
    "role_id, user_id, exp_status, exp_result",
    [
        pytest.param(
            "ab1d025b-0e33-42e2-bba8-cf7125044263",
            "afa6b9a3-5db1-4c44-b467-137394c2b167",
            HTTPStatus.NO_CONTENT,
            None,
            id="correct revoke",
        ),
        pytest.param(
            "11111111-b076-4cda-8851-aa056e96725f",
            "afa6b9a3-5db1-4c44-b467-137394c2b167",
            HTTPStatus.BAD_REQUEST,
            "The requested resource was not found",
            id="non-exist role",
        ),
        pytest.param(
            "ab1d025b-0e33-42e2-bba8-cf7125044263",
            "11111111-b076-4cda-8851-aa056e96725f",
            HTTPStatus.BAD_REQUEST,
            "The requested resource was not found",
            id="non-exist user",
        ),
    ],
)
@pytest.mark.asyncio
async def test_revoke_role(
    make_request: Callable[
        [RequestMethods, str, str, str, Any], ClientResponse
    ],
    role_id: str,
    user_id: str,
    exp_status: HTTPStatus,
    exp_result: str | None,
) -> None:
    response = await make_request(
        RequestMethods.POST,
        "/role",
        "/revoke",
        "",
        {"role_id": role_id, "user_id": user_id},
    )
    body = await response.json()

    assert response.status == exp_status

    if exp_status != HTTPStatus.NO_CONTENT:
        assert body.get("detail").startswith(exp_result)


@pytest.mark.parametrize(
    "role_id, exp_status, exp_result",
    [
        pytest.param(
            "bef8c6fd-989b-4bb3-848a-89414eadc38f",
            HTTPStatus.NO_CONTENT,
            None,
            id="correct delete",
        ),
        pytest.param(
            "11111111-b076-4cda-8851-aa056e96725f",
            HTTPStatus.BAD_REQUEST,
            "The requested resource was not found",
            id="non-exist role",
        ),
    ],
)
@pytest.mark.asyncio
async def test_delete_role(
    make_request: Callable[
        [RequestMethods, str, str, str, Any], ClientResponse
    ],
    role_id: str,
    exp_status: HTTPStatus,
    exp_result: str | None,
) -> None:
    response = await make_request(RequestMethods.DELETE, "/role", "", role_id)
    body = await response.json()

    assert response.status == exp_status

    if exp_status != HTTPStatus.NO_CONTENT:
        assert body.get("detail") == exp_result

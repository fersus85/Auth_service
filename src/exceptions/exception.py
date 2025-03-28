from typing import Any, Callable, Coroutine

import sqlalchemy.exc
from fastapi import Request, Response

from exceptions import errors
from exceptions.exc_handlers import (
    integrity_error_handler,
    no_result_error_400_handler,
    no_result_error_handler,
    password_or_login_error_handler,
    role_service_error_handler,
    unauthorized_error_handler,
)

exception_handlers: dict[
    int | type[Exception],
    Callable[[Request, Exception], Coroutine[Any, Any, Response]],
] = {
    sqlalchemy.exc.IntegrityError: integrity_error_handler,
    sqlalchemy.exc.NoResultFound: no_result_error_handler,
    errors.PasswordOrLoginExc: password_or_login_error_handler,
    errors.UnauthorizedExc: unauthorized_error_handler,
    errors.NoResult: no_result_error_400_handler,
    errors.RoleServiceExc: role_service_error_handler,
}

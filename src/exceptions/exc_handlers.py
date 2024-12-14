from fastapi import Request, Response, status
from fastapi.responses import JSONResponse


async def integrity_error_handler(
    _: Request,
    __: Exception,
) -> Response:
    """Integrity error handler."""
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={
            "detail": "Record already exists",
        },
    )


async def no_result_error_handler(
    _: Request,
    __: Exception,
) -> Response:
    """No result error handler."""
    return JSONResponse(
        status_code=status.HTTP_204_NO_CONTENT,
        content={
            "detail": "The requested resource was not found",
        },
    )


async def password_or_login_error_handler(
    _: Request,
    __: Exception,
) -> Response:
    """Not valid password or login error handler"""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "detail": "Password length must > 7 and login length > 3",
        },
    )

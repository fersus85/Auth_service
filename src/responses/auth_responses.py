from fastapi import status

from schemas.auth import UserLoginResponse
from schemas.user import UserRead, UserUpdate


def get_content(context: str) -> dict:
    return {"content": {"application/json": {"example": {"detail": context}}}}


def get_signup_response():
    resp = {
        status.HTTP_201_CREATED: {
            "description": "User successfully registered",
            "model": UserRead,
        },
        status.HTTP_400_BAD_REQUEST: {
            "description": "Not valid password or login length",
            **get_content("Password length must > 7 and login length > 3"),
        },
        status.HTTP_409_CONFLICT: {
            "description": "Login already exists",
            **get_content("Record already exists"),
        },
    }
    return resp


def get_login_response():
    resp = {
        status.HTTP_200_OK: {
            "description": "Successfull login",
            "model": UserLoginResponse,
        },
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Invalid login or password",
            **get_content("Invalid login or password"),
        },
        status.HTTP_409_CONFLICT: {
            "description": "Session already exists",
            **get_content("Record already exists"),
        },
    }
    return resp


def get_token_refr_response():
    resp = {
        status.HTTP_200_OK: {
            "description": "Get new access and refresh tokens",
            "model": UserLoginResponse,
        },
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Invalid token",
            **get_content("Token is invalid"),
            **get_content("Token expired"),
        },
    }
    return resp


def get_change_psw_response():
    resp = {
        status.HTTP_200_OK: {
            "description": "User password update success",
            "model": UserUpdate,
        },
        status.HTTP_400_BAD_REQUEST: {
            "description": "Not valid password or login length",
            **get_content("Password length must > 7 and login length > 3"),
        },
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Invalid token",
            **get_content("Token is invalid"),
            **get_content("Token expired"),
        },
    }
    return resp

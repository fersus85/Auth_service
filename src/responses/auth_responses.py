from fastapi import status

from schemas.user import UserRead


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
            "model": UserRead,
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

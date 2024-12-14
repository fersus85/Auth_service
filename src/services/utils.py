from datetime import datetime, timedelta
from typing import List, Dict, Any
from uuid import UUID, uuid4

import jwt
from fastapi import Depends, HTTPException, Request, status

from core.config import settings
from db.casher import AbstractCache, get_cacher
from schemas.auth import AccessJWT


async def decode_jwt_token(encoded_jwt_token: str):
    token_dict = jwt.decode(
        encoded_jwt_token,
        settings.JWT_TOKEN_SECRET_KEY,
        algorithms=[settings.JWT_TOKEN_ALGORITHM],
    )
    return token_dict


async def generate_new_tokens(user_id: UUID, roles: List[str]):
    now = datetime.now()
    expire_for_access_token = now + timedelta(
        minutes=settings.JWT_TOKEN_EXPIRE_TIME_M
    )
    expire_for_refresh_token = now + timedelta(
        minutes=settings.JWT_TOKEN_EXPIRE_TIME_M * 100
    )

    access_token_dict = {
        "user_id": str(user_id),
        "iat": now.timestamp(),
        "roles": roles,
    }
    refresh_token_dict = access_token_dict.copy()

    access_token_dict.update(
        {"jti": str(uuid4()), "exp": expire_for_access_token}
    )
    refresh_token_dict.update(
        {"jti": str(uuid4()), "exp": expire_for_refresh_token}
    )

    access_token_encoded_jwt = jwt.encode(
        access_token_dict,
        settings.JWT_TOKEN_SECRET_KEY,
        algorithm=settings.JWT_TOKEN_ALGORITHM,
    )
    refresh_token_encoded_jwt = jwt.encode(
        refresh_token_dict,
        settings.JWT_TOKEN_SECRET_KEY,
        algorithm=settings.JWT_TOKEN_ALGORITHM,
    )

    return (access_token_encoded_jwt, refresh_token_encoded_jwt)


def get_access_token_from_cookies(request: Request):

    token = request.cookies.get("access_token")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token not found",
        )

    return token


async def get_user_id_from_access_token(
    access_token: str = Depends(get_access_token_from_cookies),
):

    try:
        payload = jwt.decode(
            access_token,
            settings.JWT_TOKEN_SECRET_KEY,
            algorithms=settings.JWT_TOKEN_ALGORITHM,
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is invalid.",
        )

    expire = payload.get("exp")
    expire_time = datetime.fromtimestamp(int(expire))
    if (not expire) or (expire_time < datetime.now()):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is expired.",
        )

    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User ID not found.",
        )

    token_id = payload.get("jti")
    cacher: AbstractCache = await get_cacher()
    token_is_in_blacklist = await cacher.get(f"blacklist:{token_id}")
    if token_is_in_blacklist:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is in blacklist.",
        )

    return user_id


def get_refresh_token_from_cookies(request: Request):

    token = request.cookies.get("refresh_token")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found",
        )

    return token


async def get_user_id_from_refresh_token(
    refresh_token: str = Depends(get_refresh_token_from_cookies),
):

    try:
        payload = jwt.decode(
            refresh_token,
            settings.JWT_TOKEN_SECRET_KEY,
            algorithms=settings.JWT_TOKEN_ALGORITHM,
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Токен не валидный!",
        )

    expire = payload.get("exp")
    expire_time = datetime.fromtimestamp(int(expire))
    if (not expire) or (expire_time < datetime.now()):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Токен истек"
        )

    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Не найден ID пользователя",
        )

    return user_id


async def get_params_from_refresh_token(
    refresh_token: str = Depends(get_refresh_token_from_cookies),
) -> AccessJWT:
    try:
        payload = jwt.decode(
            refresh_token,
            settings.JWT_TOKEN_SECRET_KEY,
            algorithms=settings.JWT_TOKEN_ALGORITHM,
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Токен не валидный!",
        )

    if msg := check_token_payload_valid(payload):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=msg,
        )

    decoded = AccessJWT(
        jti=UUID(payload["jti"]),
        user_id=UUID(payload["user_id"]),
        iat=payload["iat"],
        exp=payload["exp"],
        roles=payload["roles"],
    )
    return decoded


def check_token_payload_valid(payload: Dict[str, Any]) -> str:
    expire = payload.get("exp")
    expire_time = datetime.fromtimestamp(int(expire))
    if (not expire) or (expire_time < datetime.now()):
        return "Токен истек"

    user_id = payload.get("user_id")
    if not user_id:
        return "Не найден ID пользователя"

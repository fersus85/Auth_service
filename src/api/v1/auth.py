import logging

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from db.casher import AbstractCache, get_cacher
from db.postrges_db.psql import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    response_model=BaseModel,
    summary="Temporary endpont for test",
    description="Temporary endpont for test",
)
async def auth(
    db: AsyncSession = Depends(get_db),
    cacher: AbstractCache = Depends(get_cacher),
):
    try:
        result = await db.execute(text("SELECT 1"))
        await cacher.set("Try", "probe", 180)
        data = await cacher.get("Try")
        value = result.scalar()
        return {
            "res": value,
            "msg": "Database connection is working!",
            "from_cache": data,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/signup",
    status_code=status.HTTP_201_CREATED,
    response_model=BaseModel,
    summary="User registration",
    description="User registration endpoint",
)
async def signup_user() -> BaseModel:
    return {}


@router.post(
    "/login",
    status_code=status.HTTP_200_OK,
    response_model=BaseModel,
    summary="User login",
    description="User login endpoint returns access and refresh tokens",
)
async def login_user() -> BaseModel:
    return {}


@router.post(
    "/social-login",
    response_model=BaseModel,
    status_code=status.HTTP_200_OK,
    summary="OAuth 2.0 login",
    description="OAuth 2.0 login",
)
async def social_login() -> BaseModel:
    return {}


@router.post(
    "/token/refresh",
    status_code=status.HTTP_200_OK,
    response_model=BaseModel,
    summary="New access and refresh tokens",
    description="Get new access and refresh tokens",
)
async def refresh_token() -> BaseModel:
    return {}


@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    response_model=BaseModel,
    summary="User logout",
    description="User logout endpoint",
)
async def logout_user() -> BaseModel:
    return {}


@router.post(
    "/password_update",
    response_model=BaseModel,
    status_code=status.HTTP_200_OK,
    summary="User password update",
    description="User password update endpoint",
)
async def password_update() -> BaseModel:
    return {}


@router.post(
    "/verify",
    response_model=BaseModel,
    status_code=status.HTTP_200_OK,
    summary="User permissions verify",
    description="User permissions verify endpoint",
)
async def verify_role() -> BaseModel:
    return {}

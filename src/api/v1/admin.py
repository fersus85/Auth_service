from typing import Any

from fastapi import APIRouter, status
from pydantic import BaseModel

router = APIRouter(prefix="/role", tags=["Admin"])


@router.get(
    "/{role_id}",
    response_model=BaseModel,
    status_code=status.HTTP_200_OK,
    summary="Role info",
    description="Role info endpoint",
)
async def role_info(role_id: str) -> Any:
    return {}


@router.post(
    "/",
    response_model=BaseModel,
    status_code=status.HTTP_201_CREATED,
    summary="Role creation",
    description="Role creation endpoint",
)
async def create_role() -> BaseModel:
    return {}


@router.put(
    "/{role_id}",
    response_model=BaseModel,
    status_code=status.HTTP_200_OK,
    summary="Role update",
    description="Role update endpoint",
)
async def update_role(role_id: str) -> BaseModel:
    return {}


@router.delete(
    "/{role_id}",
    response_model=BaseModel,
    status_code=status.HTTP_200_OK,
    summary="Role deletion",
    description="Role deletion endpoint",
)
async def delete_role(role_id: str) -> BaseModel:
    return {}


@router.get(
    "s",
    response_model=BaseModel,
    status_code=status.HTTP_200_OK,
    summary="Roles list",
    description="Roles list endpoint",
)
async def list_roles() -> Any:
    return {}


@router.post(
    "/assign",
    response_model=BaseModel,
    status_code=status.HTTP_200_OK,
    summary="Assign roles to user",
    description="Assign roles to user",
)
async def assign_role() -> BaseModel:
    return {}


@router.post(
    "/revoke",
    response_model=BaseModel,
    status_code=status.HTTP_200_OK,
    summary="Revoke roles from user",
    description="Revoke roles from user",
)
async def revoke_role() -> BaseModel:
    return {}

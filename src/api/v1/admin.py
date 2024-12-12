from typing import Any

from fastapi import APIRouter, status, Depends
from pydantic import BaseModel

from schemas.role import RoleCreate, RoleRead
from services.role.role_service import get_role_service, RoleService
import logging

logger = logging.getLogger(__name__)

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
    response_model=RoleRead,
    status_code=status.HTTP_201_CREATED,
    summary="Role creation",
    description="Role creation endpoint",
)
async def create_role(
    role_create: RoleCreate,
    role_service: RoleService = Depends(get_role_service),
) -> RoleRead:
    result = await role_service.create(role_create)
    logger.info(f"create_role result = {result}")
    return result


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

import logging
from typing import List
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from fastapi.params import Depends

from responses.admin_responses import (
    get_role_assign_response,
    get_role_create_response,
    get_role_del_response,
    get_role_info_response,
    get_role_upd_response,
)
from schemas.role import RoleAssign, RoleCreate, RoleRead, RoleUpdate
from services.helpers import PermissionChecker
from services.role.role_service import RoleService, get_role_service

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/role",
    tags=["Admin"],
    dependencies=[Depends(PermissionChecker(required={"admin", "superuser"}))],
)


@router.get(
    "/{role_id}",
    response_model=RoleRead,
    status_code=status.HTTP_200_OK,
    summary="Role info",
    description="Role info endpoint",
    responses=get_role_info_response(),
)
async def role_info(
    role_id: UUID, role_service: RoleService = Depends(get_role_service)
) -> RoleRead:
    if (role := await role_service.get(role_id)) is None:
        raise HTTPException(status_code=404, detail="Role not found")
    return role


@router.post(
    "/",
    response_model=RoleRead,
    status_code=status.HTTP_201_CREATED,
    summary="Role creation",
    description="Role creation endpoint",
    responses=get_role_create_response(),
)
async def create_role(
    role: RoleCreate, role_service: RoleService = Depends(get_role_service)
) -> RoleRead:
    result = await role_service.create(role)
    logger.info(f"create_role result = {result}")
    return result


@router.put(
    "/{role_id}",
    response_model=RoleRead,
    status_code=status.HTTP_200_OK,
    summary="Role update",
    description="Role update endpoint",
    responses=get_role_upd_response(),
)
async def update_role(
    role_id: UUID,
    role_update: RoleUpdate,
    role_service: RoleService = Depends(get_role_service),
) -> RoleRead:
    role = await role_service.update(role_id, role_update)
    if role is None:
        raise HTTPException(status_code=404, detail="Role not found")
    return role


@router.delete(
    "/{role_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Role deletion",
    description="Role deletion endpoint",
    responses=get_role_del_response(),
)
async def delete_role(
    role_id: UUID, role_service: RoleService = Depends(get_role_service)
) -> None:
    await role_service.delete(role_id)


@router.get(
    "/list/",
    response_model=List[RoleRead],
    status_code=status.HTTP_200_OK,
    summary="Roles list",
    description="Roles list endpoint",
)
async def list_roles(
    query: str | None = None,
    role_service: RoleService = Depends(get_role_service),
) -> List[RoleRead]:
    return await role_service.list_roles(query)


@router.post(
    "/assign",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Assign roles to user",
    description="Assign roles to user",
    responses=get_role_assign_response(),
)
async def assign_role(
    body: RoleAssign,
    role_service: RoleService = Depends(get_role_service),
) -> None:
    return await role_service.assign(body.role_id, body.user_id)


@router.post(
    "/revoke",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke roles from user",
    description="Revoke roles from user",
    responses=get_role_assign_response(),
)
async def revoke_role(
    body: RoleAssign,
    role_service: RoleService = Depends(get_role_service),
) -> None:
    return await role_service.revoke(body.role_id, body.user_id)

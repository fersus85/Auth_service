import logging
from typing import List
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from fastapi.params import Depends

from schemas.role import RoleCreate, RoleRead, RoleUpdate
from services.helpers import PermissionChecker
from services.role import NoResult, RoleServiceExc
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
)
async def create_role(
    role: RoleCreate, role_service: RoleService = Depends(get_role_service)
) -> RoleRead:
    try:
        result = await role_service.create(role)
        logger.info(f"create_role result = {result}")
        return result
    except RoleServiceExc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Role with this name already exists",
        )


@router.put(
    "/{role_id}",
    response_model=RoleRead,
    status_code=status.HTTP_200_OK,
    summary="Role update",
    description="Role update endpoint",
)
async def update_role(
    role_id: UUID,
    role_update: RoleUpdate,
    role_service: RoleService = Depends(get_role_service),
) -> RoleRead:
    if (role := await role_service.update(role_id, role_update)) is None:
        raise HTTPException(status_code=404, detail="Role not found")
    return role


@router.delete(
    "/{role_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Role deletion",
    description="Role deletion endpoint",
)
async def delete_role(
    role_id: UUID, role_service: RoleService = Depends(get_role_service)
) -> None:
    try:
        await role_service.delete(role_id)
    except NoResult:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No role with id {role_id} found",
        )


@router.get(
    "s",
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
)
async def assign_role(
    role_id: UUID,
    user_id: UUID,
    role_service: RoleService = Depends(get_role_service),
) -> None:
    try:
        return await role_service.assign(role_id, user_id)
    except RoleServiceExc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to assign role to the user",
        )


@router.post(
    "/revoke",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke roles from user",
    description="Revoke roles from user",
)
async def revoke_role(
    role_id: UUID,
    user_id: UUID,
    role_service: RoleService = Depends(get_role_service),
) -> None:
    try:
        return await role_service.revoke(role_id, user_id)
    except NoResult:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No role {role_id} assigned to user {user_id}",
        )

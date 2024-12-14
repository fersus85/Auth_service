from fastapi import status

from schemas.role import RoleRead


def get_content(context: str) -> dict:
    return {"content": {"application/json": {"example": {"detail": context}}}}


def get_role_info_response():
    resp = {
        status.HTTP_200_OK: {
            "description": "Role info",
            "model": RoleRead,
        },
        status.HTTP_403_FORBIDDEN: {
            "description": "Not enough permissions for perform",
            **get_content("Not enough permissions"),
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Role not found",
            **get_content("Role not found"),
        },
    }
    return resp


def get_role_create_response():
    resp = {
        status.HTTP_201_CREATED: {
            "description": "Create new Role",
            "model": RoleRead,
        },
        status.HTTP_403_FORBIDDEN: {
            "description": "Not enough permissions for perform",
            **get_content("Not enough permissions"),
        },
        status.HTTP_409_CONFLICT: {
            "description": "Role with this name already exists",
            **get_content("Role with this name already exists"),
        },
    }
    return resp


def get_role_upd_response():
    resp = {
        status.HTTP_200_OK: {
            "description": "Role description update",
            "model": RoleRead,
        },
        status.HTTP_403_FORBIDDEN: {
            "description": "Not enough permissions for perform",
            **get_content("Not enough permissions"),
        },
        status.HTTP_400_BAD_REQUEST: {
            "description": "Failed to update role",
            **get_content("Failed to update role"),
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Role not found",
            **get_content("Role not found"),
        },
    }
    return resp


def get_role_del_response():
    resp = {
        status.HTTP_204_NO_CONTENT: {
            "description": "Role deletion",
        },
        status.HTTP_403_FORBIDDEN: {
            "description": "Not enough permissions for perform",
            **get_content("Not enough permissions"),
        },
        status.HTTP_400_BAD_REQUEST: {
            "description": "Failed to delete role",
            **get_content("No role with id ... found"),
        },
    }
    return resp


def get_role_assign_response():
    resp = {
        status.HTTP_204_NO_CONTENT: {
            "description": "Assign roles to user",
        },
        status.HTTP_403_FORBIDDEN: {
            "description": "Not enough permissions for perform",
            **get_content("Not enough permissions"),
        },
        status.HTTP_400_BAD_REQUEST: {
            "description": "Failed to assign role to the user",
            **get_content("Failed to assign role to the user"),
        },
    }
    return resp

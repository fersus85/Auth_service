from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/profile", tags=["User"])


@router.get(
    "/",
    response_model=BaseModel,
    summary="User's profile",
    description="Get user's profile",
)
async def get_profile() -> BaseModel:
    return {}


@router.get(
    "/history",
    response_model=BaseModel,
    summary="User's login history",
    description="Get user's login history",
)
async def login_history() -> BaseModel:
    return {}


@router.get(
    "/linked-accounts",
    response_model=BaseModel,
    summary="Linked accounts",
    description="Get linked Accounts",
)
async def get_linked_accounts() -> BaseModel:
    return {}


@router.delete(
    "/linked-accounts/{account_id}",
    response_model=BaseModel,
    summary="Unlink account",
    description="Unlink account",
)
async def unlink_account() -> BaseModel:
    return {}

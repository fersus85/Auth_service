import logging
from typing import List

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from schemas.session import HistoryRead
from schemas.user import UserRead
from services.user.user_service import UserService, get_user_service
from services.utils import get_user_id_from_access_token

router = APIRouter(prefix="/profile", tags=["User"])

logger = logging.getLogger(__name__)


@router.get(
    "/",
    response_model=UserRead,
    summary="User's profile",
    description="Get user's profile",
)
async def get_profile(
    user_service: UserService = Depends(get_user_service),
    user_id: str = Depends(get_user_id_from_access_token),
) -> UserRead:
    """
    Вывод инф-ии о текущем пользователе.
    """
    result = await user_service.get_profile(user_id)
    logger.info(f"get_profile result = {result}")
    return result


@router.get(
    "/history",
    response_model=List[HistoryRead],
    summary="User's login history",
    description="Get user's login history",
)
async def login_history(
    user_service: UserService = Depends(get_user_service),
    user_id: str = Depends(get_user_id_from_access_token),
) -> List[HistoryRead]:
    """
    Вывод истории сессий текущего пользователя.
    """
    result = await user_service.get_history(user_id)
    logger.info(f"login_history result = {result}")
    return result


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

import logging

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel

from responses.auth_responses import get_history_response, get_profile_response
from schemas.session import HistoryRead
from schemas.user import UserRead
from services.user.user_service import UserService, get_user_service
from services.utils import get_user_id_from_access_token

router = APIRouter(prefix="/profile", tags=["User"])

logger = logging.getLogger(__name__)


@router.get(
    "/",
    response_model=UserRead,
    status_code=status.HTTP_200_OK,
    summary="User's profile",
    description="Get user's profile",
    responses=get_profile_response(),
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
    response_model=HistoryRead,
    summary="User's login history",
    description="Get user's login history",
    responses=get_history_response(),
)
async def login_history(
    page_size: int = Query(
        10, ge=1, le=50, description="Кол-во событий на странице (1-50)"
    ),
    page_number: int = Query(1, ge=1, description="Номер страницы"),
    user_service: UserService = Depends(get_user_service),
    user_id: str = Depends(get_user_id_from_access_token),
) -> HistoryRead:
    """
    Вывод истории сессий текущего пользователя.
    """
    result = await user_service.get_history(user_id, page_size, page_number)
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

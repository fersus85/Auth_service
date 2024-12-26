import logging
from typing import Annotated
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, Header, Query, Response, status

from core.config import settings
from schemas.yndx_oauth import UserInfoSchema
from services.auth.auth_service import AuthService, get_auth_service
from services.helpers import (
    set_tokens_in_cookies,
    yndx_info_request,
    yndx_token_request,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/oauth", tags=["OAuth 2.0"])


@router.get(
    "/yndx_social_login",
    status_code=status.HTTP_200_OK,
    summary="OAuth 2.0 Yndx login",
    description="Redirects to Yandex OAuth 2.0 login page.",
)
async def yndx_social_login():
    params = {
        "response_type": "code",
        "client_id": settings.yndx_oauth.YNDX_CLIENT_ID,
    }
    auth_url = f"{settings.yndx_oauth.YNDX_CODE_URL}?{urlencode(params)}"
    logger.warning("url: %s", auth_url)
    return {"url_for_auth": auth_url}


@router.get(
    "/yndx_callback",
    response_model="",
    status_code=status.HTTP_200_OK,
    summary="OAuth 2.0 Yndx login callback",
    description="Login user via Yandex OAuth 2.0",
)
async def yndx_callback(
    response: Response,
    code: str = Query(
        ...,
        title="code",
        description="Код подтверждения аутентификации в Yandex",
    ),
    auth_service: AuthService = Depends(get_auth_service),
    user_agent: Annotated[str | None, Header()] = None,
):
    resp_token_dict = await yndx_token_request(code)
    logger.warning("Response YNDX_TOKEN_URL: %s", resp_token_dict)

    resp_info_dict = await yndx_info_request(resp_token_dict)
    logger.warning("Response YNDX_INFO_URL: %s", resp_info_dict)

    user_info = UserInfoSchema(**resp_info_dict)
    user, tokens = await auth_service.login_user_yndx(user_info, user_agent)

    set_tokens_in_cookies(response, tokens)

    return user

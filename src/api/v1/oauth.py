import logging
import random
import string
from typing import Annotated
from urllib.parse import urlencode

import pkce
from fastapi import (
    APIRouter,
    Depends,
    Header,
    Query,
    Request,
    Response,
    status,
)
from fastapi.responses import RedirectResponse

from core.config import settings
from schemas.yndx_oauth import UserInfoSchema
from services.auth.auth_service import AuthService, get_auth_service
from services.helpers import (
    convert_vk_user_info_to_yndx,
    set_tokens_in_cookies,
    vk_info_request,
    vk_token_request,
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


@router.get(
    "/vk_social_login",
    status_code=status.HTTP_200_OK,
    summary="OAuth 2.0 VK login",
    description="Redirects to VK OAuth 2.0 login page.",
)
async def vk_social_login(
    response: Response,
):

    state = "".join(
        random.choices(string.ascii_uppercase + string.digits, k=32)
    )
    code_verifier, code_challenge = pkce.generate_pkce_pair()

    params = {
        "response_type": "code",
        "client_id": settings.vk_oauth.VK_CLIENT_ID,
        "redirect_uri": "https://localhost/api/v1/oauth/vk_callback",
        "state": state,
        "scope": "email phone",
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }
    auth_url = f"{settings.vk_oauth.VK_CODE_URL}?{urlencode(params)}"

    response = RedirectResponse(auth_url)

    response.set_cookie(
        key="vk_oauth_state",
        value=state,
        httponly=True,
        samesite="lax",
    )

    response.set_cookie(
        key="vk_oauth_code_verifier",
        value=code_verifier,
        httponly=True,
        samesite="lax",
    )

    return response


@router.get(
    "/vk_callback",
    response_model="",
    status_code=status.HTTP_200_OK,
    summary="OAuth 2.0 VK login",
    description="Callback from VK OAuth 2.0 login page.",
)
async def vk_callback(
    code: str,
    device_id: str,
    state: str,
    request: Request,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
    user_agent: Annotated[str | None, Header()] = None,
):

    origin_state = request.cookies.get("vk_oauth_state")
    code_verifier = request.cookies.get("vk_oauth_code_verifier")

    if state != origin_state:
        logger.error("VK state is invalid!")

    resp_token_dict = await vk_token_request(
        code, code_verifier, device_id, state
    )

    resp_info_dict = await vk_info_request(resp_token_dict)

    # приводим словарь с user info к общему формату,
    # чтобы использовать общие ф-ии
    resp_info_dict = await convert_vk_user_info_to_yndx(resp_info_dict)

    user_info = UserInfoSchema(**resp_info_dict)
    user, tokens = await auth_service.login_user_yndx(user_info, user_agent)

    set_tokens_in_cookies(response, tokens)

    return user

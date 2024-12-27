import logging
from typing import Annotated
from urllib.parse import urlencode

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
    set_tokens_in_cookies,
    yndx_info_request,
    yndx_token_request,
)
from services.tracer import Tracer, get_tracer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/oauth", tags=["OAuth 2.0"])


@router.get(
    "/yndx_social_login",
    status_code=status.HTTP_302_FOUND,
    summary="OAuth 2.0 Yndx login",
    description="""
    ## Важно
    Для тестирования этого эндпоинта вам необходимо скопировать ссылку
    https://localhost:443/api/v1/oauth/yndx_social_login
    и вызвать ее в браузере.
    Так как Swagger UI делает xhr-запросы, при выполнении которых
    могут возникать ограничения, связанные с CORS.
    """,
)
async def yndx_social_login(
    request: Request, tracer: Tracer = Depends(get_tracer)
) -> RedirectResponse:
    request_id = request.headers.get("X-Request-Id")
    with tracer.start_span("Social login yndx") as span:
        span.set_attribute("http.request_id", request_id)
        params = {
            "response_type": "code",
            "client_id": settings.yndx_oauth.YNDX_CLIENT_ID,
        }
        auth_url = f"{settings.yndx_oauth.YNDX_CODE_URL}?{urlencode(params)}"
        logger.warning("url: %s", auth_url)
        return RedirectResponse(auth_url)


@router.get(
    "/yndx_callback",
    response_model="",
    status_code=status.HTTP_200_OK,
    summary="OAuth 2.0 Yndx login callback",
    description="""
    Логинит пользователя с помощью информации, полученной от Yandex,
    на основе кода, полученного в эндпоинте /yndx_social_login
    """,
)
async def yndx_callback(
    response: Response,
    request: Request,
    code: str = Query(
        ...,
        title="code",
        description="Код подтверждения аутентификации в Yandex",
    ),
    auth_service: AuthService = Depends(get_auth_service),
    user_agent: Annotated[str | None, Header()] = None,
    tracer: Tracer = Depends(get_tracer),
):
    request_id = request.headers.get("X-Request-Id")

    with tracer.start_span("yndx_callback") as span:
        span.set_attribute("http.request_id", request_id)

        with tracer.start_span("Request for yndx access token") as inner_span:
            inner_span.set_attribute("http.request_id", request_id)
            resp_token_dict = await yndx_token_request(code)
            logger.warning("Response YNDX_TOKEN_URL: %s", resp_token_dict)

        with tracer.start_span("Request for user info to yndx") as inner_span:
            inner_span.set_attribute("http.request_id", request_id)
            resp_info_dict = await yndx_info_request(resp_token_dict)
            logger.warning("Response YNDX_INFO_URL: %s", resp_info_dict)

        with tracer.start_span("Login user") as inner_span:
            inner_span.set_attribute("http.request_id", request_id)
            user_info = UserInfoSchema(**resp_info_dict)
            user, tokens = await auth_service.login_user_yndx(
                user_info, user_agent, request_id
            )

    set_tokens_in_cookies(response, tokens)

    return user

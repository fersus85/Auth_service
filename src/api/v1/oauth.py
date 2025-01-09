import logging
from typing import Annotated, Literal
from urllib.parse import urlencode

from fastapi import (
    APIRouter,
    Depends,
    Header,
    HTTPException,
    Query,
    Request,
    Response,
    status,
)
from fastapi.responses import RedirectResponse
from google_auth_oauthlib.flow import Flow as GoogleFlow
from googleapiclient.discovery import build

from core.config import AuthFlow as a_fl
from core.config import settings
from schemas.user import UserBase
from schemas.yndx_oauth import UserInfoSchema
from services.auth.auth_service import AuthService, get_auth_service
from services.helpers import (
    convert_vk_user_info_to_yndx,
    set_code_state_in_cookies,
    set_tokens_in_cookies,
    vk_info_request,
    vk_token_request,
    yndx_info_request,
    yndx_token_request,
)
from services.tracer import Tracer, get_tracer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/oauth", tags=["OAuth 2.0"])
google_router = APIRouter(prefix="/google", tags=["Google OAuth 2.0"])


@router.get(
    "/social_login",
    status_code=status.HTTP_302_FOUND,
    summary="OAuth 2.0 login",
    description="""
    ## Важно
    Так как Swagger UI делает xhr-запросы, при выполнении которых
    могут возникать ограничения, связанные с CORS:
    тестировать можно только вручную, через панель разработчика в браузере
    """,
)
async def social_login(
    request: Request,
    tracer: Tracer = Depends(get_tracer),
    flow: Literal[a_fl.YANDEX, a_fl.VK, a_fl.GOOGLE] = Query(
        ...,
        title="auth flow",
        description="Choose the authentication flow.",
        enum=[a_fl.YANDEX, a_fl.VK, a_fl.GOOGLE],
    ),
) -> RedirectResponse:
    request_id = request.headers.get("X-Request-Id")
    match flow:
        case a_fl.YANDEX:
            with tracer.start_span("Social login yndx") as span:
                span.set_attribute("http.request_id", request_id)
                params = settings.yndx_oauth.get_client_config()
                auth_url = (
                    f"{settings.yndx_oauth.CODE_URL}?{urlencode(params)}"
                )
                logger.warning("url: %s", auth_url)
                return RedirectResponse(auth_url)
        case a_fl.VK:
            with tracer.start_span("Social login VK") as span:
                conf_dict = settings.vk_oauth.get_client_config()
                params = conf_dict["params"]
                auth_url = f"{settings.vk_oauth.CODE_URL}?{urlencode(params)}"

                response = RedirectResponse(auth_url)

                set_code_state_in_cookies(
                    response=response,
                    state=conf_dict["state"],
                    code_verifier=conf_dict["code_verifier"],
                )
                return response
        case a_fl.GOOGLE:
            with tracer.start_span("Social login Google") as span:
                g_flow = GoogleFlow.from_client_config(
                    **settings.google_oauth.get_client_config()
                )

                authorization_url, state = g_flow.authorization_url(
                    access_type="offline",
                    include_granted_scopes="true",
                    prompt="consent",
                )
                return RedirectResponse(url=authorization_url)


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
    request_id = request.headers.get("X-Request-Id")

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
    user, tokens = await auth_service.login_user_yndx(
        user_info, user_agent, request_id
    )

    set_tokens_in_cookies(response, tokens)

    return user


@google_router.get(
    "/callback",
    status_code=status.HTTP_200_OK,
    summary="OAuth 2.0 Google login callback",
    description="Login user via Google OAuth 2.0",
)
async def google_callback(
    request: Request,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
    user_agent: Annotated[str | None, Header()] = None,
):
    error = request.query_params.get("error")
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=error
        )

    flow = GoogleFlow.from_client_config(
        **settings.google_oauth.get_client_config()
    )
    flow.fetch_token(authorization_response=str(request.url))

    credentials = flow.credentials
    service = build("people", "v1", credentials=credentials)

    profile = (
        service.people()
        .get(resourceName="people/me", personFields="names,emailAddresses")
        .execute()
    )

    user = UserBase(
        login=profile["names"][0]["displayName"],
        first_name=profile["names"][0].get("givenName", ""),
        last_name=profile["names"][0].get("familyName", ""),
        # email=profile["emailAddresses"][0]["value"]
    )
    request_id = request.headers.get("X-Request-Id")
    user, tokens = await auth_service.login_user_oauth(
        user, user_agent, request_id
    )

    set_tokens_in_cookies(response, tokens)

    return user

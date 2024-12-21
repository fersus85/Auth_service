import logging

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse, ORJSONResponse

from api import router as api_router
from core.config import settings
from core.log_config import setup_logging
from exceptions.exception import exception_handlers
from lifespan import lifespan
from services.limiter import check_limit

setup_logging()
logger = logging.getLogger(__name__)


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Auth movies service",
    version="1.0.0",
    lifespan=lifespan,
    exception_handlers=exception_handlers,
    docs_url="/api/openapi",
    openapi_url="/api/openapi.json",
    default_response_class=ORJSONResponse,
)


@app.middleware("http")
async def log_stuff(request: Request, call_next):
    response = await call_next(request)
    logger.info(f"{response.status_code} {request.method} {request.url}")
    return response


@app.middleware("http")
async def limiter(request: Request, call_next):
    limit_result = await check_limit()
    if limit_result:
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS, content=None
        )
    response = await call_next(request)
    return response


app.include_router(api_router, prefix="/api")

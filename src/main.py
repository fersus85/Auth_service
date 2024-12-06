import logging

from fastapi import FastAPI, Request
from fastapi.responses import ORJSONResponse

from api.v1 import auth
from core.config import settings
from core.log_config import setup_logging
from lifespan import lifespan

setup_logging()
logger = logging.getLogger(__name__)


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Auth movies service",
    version="1.0.0",
    lifespan=lifespan,
    root_path="/api",
    docs_url="/openapi",
    openapi_url="/openapi.json",
    default_response_class=ORJSONResponse,
)


@app.middleware("http")
async def log_stuff(request: Request, call_next):
    response = await call_next(request)
    logger.info(f"{response.status_code} {request.method} {request.url}")
    return response


# Просто для проверки работоспособности сервиса, потом уберём
app.include_router(auth.router, prefix="/v1/auth", tags=["auth"])

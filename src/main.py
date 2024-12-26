import logging

from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

from api import router as api_router
from core.config import settings
from core.log_config import setup_logging
from exceptions.exception import exception_handlers
from lifespan import lifespan
from middlewares import before_request, limiter, log_stuff
from tracer import configure_tracer

setup_logging()
logger = logging.getLogger(__name__)

configure_tracer()


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

FastAPIInstrumentor.instrument_app(app)

app.middleware("http")(log_stuff)
app.middleware("http")(limiter)
app.middleware("http")(before_request)


app.include_router(api_router, prefix="/api")

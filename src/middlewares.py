import logging

from fastapi import Request, status
from fastapi.responses import JSONResponse, ORJSONResponse, Response

from db.redis import Redis, get_redis
from services.limiter import RateLimiter

logger = logging.getLogger(__name__)


async def log_stuff(request: Request, call_next):
    response: Response = await call_next(request)
    logger.info(f"{response.status_code} {request.method} {request.url}")
    return response


async def limiter(request: Request, call_next):
    redis: Redis = await get_redis()

    limiter = RateLimiter(redis)

    limit_result = await limiter.check_limit()
    if limit_result:
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS, content=None
        )
    response = await call_next(request)
    return response


async def before_request(request: Request, call_next):
    response = await call_next(request)
    request_id = request.headers.get("X-Request-Id")
    if not request_id:
        return ORJSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": "X-Request-Id is required"},
        )
    return response

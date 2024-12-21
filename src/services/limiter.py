import datetime
import logging

from core.config import settings
from db.redis import Redis

logger = logging.getLogger(__name__)


class RateLimiter:

    def __init__(self, redis):
        self.redis: Redis = redis

    async def check_limit(self):

        pipe = self.redis.pipeline()
        now = datetime.datetime.now()
        key = f"limit:{now.second}"
        pipe.incr(key, 1)
        pipe.expire(key, 2)
        result = await pipe.execute()
        request_number = result[0]
        if request_number > settings.REQUEST_LIMIT_PER_SECOND:
            logger.warning(
                "Request limit exceeded: %s requests in one second",
                request_number,
            )
            return True
        return False

    async def __aenter__(self):
        return self

    async def __aexit__(self, type, value, traceback):
        await self.redis.close()

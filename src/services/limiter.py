import datetime

from core.config import settings
from db.redis import Redis, get_redis


async def check_limit():
    cache: Redis = await get_redis()

    pipe = cache.pipeline()
    now = datetime.datetime.now()
    key = f"limit:{now.second}"
    pipe.incr(key, 1)
    pipe.expire(key, 2)
    result = await pipe.execute()
    request_number = result[0]
    if request_number > settings.REQUEST_LIMIT_PER_SECOND:
        return True
    return False

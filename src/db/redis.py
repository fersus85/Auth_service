import logging
import pickle
from functools import wraps
from hashlib import sha256
from typing import Any, Callable, Optional

from redis.asyncio import Redis

from db.casher import AbstractCache

logger = logging.getLogger(__name__)


class RedisCache(AbstractCache):
    """Реализация кэша с помощью Redis"""

    def __init__(self, cache_type: Redis) -> None:
        self.cacher = cache_type

    async def set(self, key: str, value: Any, expire: int) -> None:
        try:
            await self.cacher.set(key, pickle.dumps(value), ex=expire)
            logger.debug("Result stored in cache")
        except Exception as ex:
            logger.error("Error storing to cache: %s", ex)

    async def get(self, key: str) -> Optional[Any]:
        try:
            cache_value = await self.cacher.get(key)
            return pickle.loads(cache_value) if cache_value else None
        except Exception as ex:
            logger.error("Error retrieving from cache: %s", ex)
            return None


redis: Optional[Redis] = None


async def get_redis() -> Redis:
    return redis


def form_key(*args, **kwargs) -> str:
    return sha256(pickle.dumps((args, kwargs))).hexdigest()


def cache_method(cache_attr: str, expire: int = 1800):
    """
    cache_method is a decorator that caches the result
    of an asynchronous method in a store.

    Parameters:
    - cache_attr (str): The attribute name for the instance
                        of store in the class.
    - expire (int): The cache expiration time in seconds.
                    Defaults to 1800 seconds (30 minutes).

    Raises:
    - ValueError: If the cacher instance is not set.
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            cache = getattr(self, cache_attr, None)

            if cache is None:
                raise ValueError("Cache instance is not set")

            key = form_key(func.__name__, args, kwargs)

            cache_result = await cache.get(key)
            if cache_result is not None:
                logger.debug("Response from cache")
                return cache_result

            result = await func(self, *args, **kwargs)
            await cache.set(key, result, expire)
            return result

        return wrapper

    return decorator

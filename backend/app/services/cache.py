"""Redis-backed API response cache."""
import json
from functools import wraps
from typing import Any, Callable, TypeVar

import redis.asyncio as redis

from app.config import settings

F = TypeVar("F", bound=Callable[..., Any])

_redis: redis.Redis | None = None


async def get_redis() -> redis.Redis | None:
    """Get Redis connection for caching."""
    global _redis
    if _redis is None:
        try:
            _redis = redis.from_url(settings.redis_url, decode_responses=True)
        except Exception:
            return None
    return _redis


def cache_response(ttl_seconds: int | None = None):
    """Decorator to cache async endpoint responses in Redis."""
    ttl = ttl_seconds or settings.api_cache_ttl_seconds

    def decorator(func: F) -> F:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            r = await get_redis()
            if not r:
                return await func(*args, **kwargs)
            key = f"cache:{func.__module__}:{func.__name__}"
            for a in args:
                if hasattr(a, "id"):
                    key += f":{a.id}"
                    break
            try:
                cached = await r.get(key)
                if cached:
                    return json.loads(cached)
            except Exception:
                pass
            result = await func(*args, **kwargs)
            try:
                await r.setex(key, ttl, json.dumps(result, default=str))
            except Exception:
                pass
            return result

        return wrapper  # type: ignore

    return decorator

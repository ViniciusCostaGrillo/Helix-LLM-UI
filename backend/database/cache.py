import functools
import json
import logging
import time
from typing import Any, Callable, Dict, Optional

from backend.database.redis_client import MockRedis, RedisClientManager

logger = logging.getLogger(__name__)


class MockCache:
    """In-memory thread-safe mock cache representation."""

    def __init__(self) -> None:
        self._store: Dict[str, str] = {}
        self._expires: Dict[str, float] = {}

    def get(self, key: str) -> Optional[str]:
        if key in self._expires:
            if time.time() > self._expires[key]:
                self.delete(key)
                return None
        return self._store.get(key)

    def set(self, key: str, value: str, expire: Optional[int] = None) -> None:
        self._store[key] = value
        if expire:
            self._expires[key] = time.time() + expire

    def delete(self, key: str) -> None:
        self._store.pop(key, None)
        self._expires.pop(key, None)

    def clear(self) -> None:
        self._store.clear()
        self._expires.clear()

    def ping(self) -> bool:
        return True


_cached_mock_cache = None


class CacheManager:
    """Manages system caching utilizing Redis or local in-memory MockCache."""

    def __init__(self) -> None:
        global _cached_mock_cache
        self.redis_manager = RedisClientManager()
        self.client = self.redis_manager.get_client()
        if isinstance(self.client, MockRedis):
            if _cached_mock_cache is None:
                _cached_mock_cache = MockCache()
            self.cache = _cached_mock_cache
        else:
            self.cache = self.client


    def get(self, key: str) -> Optional[Any]:
        try:
            val = self.cache.get(key)
            if val:
                return json.loads(val)
        except Exception as e:
            logger.error(f"Cache get error for key '{key}': {e}")
        return None

    def set(self, key: str, value: Any, expire_seconds: Optional[int] = None) -> None:
        try:
            serialized = json.dumps(value)
            if hasattr(self.cache, "setex") and expire_seconds:
                self.cache.setex(key, expire_seconds, serialized)
            else:
                self.cache.set(key, serialized, expire=expire_seconds)
        except Exception as e:
            logger.error(f"Cache set error for key '{key}': {e}")

    def delete(self, key: str) -> None:
        try:
            self.cache.delete(key)
        except Exception as e:
            logger.error(f"Cache delete error for key '{key}': {e}")

    def clear(self) -> None:
        try:
            if hasattr(self.cache, "flushdb"):
                self.cache.flushdb()
            else:
                self.cache.clear()
        except Exception as e:
            logger.error(f"Cache clear error: {e}")


def cache_response(expire_seconds: int = 60) -> Callable[..., Any]:
    """Decorator to cache results of sync or async functions."""
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        import asyncio

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            cache_mgr = CacheManager()
            key = f"cache:{func.__module__}:{func.__name__}:{args}:{kwargs}"
            cached_val = cache_mgr.get(key)
            if cached_val is not None:
                logger.debug(f"Cache HIT for key: {key}")
                return cached_val

            logger.debug(f"Cache MISS for key: {key}")
            val = func(*args, **kwargs)
            cache_mgr.set(key, val, expire_seconds)
            return val

        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            cache_mgr = CacheManager()
            key = f"cache:{func.__module__}:{func.__name__}:{args}:{kwargs}"
            cached_val = cache_mgr.get(key)
            if cached_val is not None:
                logger.debug(f"Cache HIT for key: {key}")
                return cached_val

            logger.debug(f"Cache MISS for key: {key}")
            val = await func(*args, **kwargs)
            cache_mgr.set(key, val, expire_seconds)
            return val

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator

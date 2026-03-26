import time
from functools import wraps
from typing import Any
from utils.logger_handler import logger


class CacheManager:
    """简单的内存缓存管理器"""

    def __init__(self, default_ttl: int = 600):
        self._cache: dict[str, dict[str, Any]] = {}
        self._timestamps: dict[str, float] = {}
        self.default_ttl = default_ttl

    def get(self, key: str) -> Any | None:
        """从缓存获取数据"""
        if key not in self._cache:
            return None

        if time.time() - self._timestamps[key] > self.default_ttl:
            logger.debug(f"[Cache] 缓存键{key}已过期")
            del self._cache[key]
            del self._timestamps[key]
            return None

        logger.debug(f"[Cache] 命中缓存：{key}")
        return self._cache[key]

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """设置缓存"""
        self._cache[key] = value
        self._timestamps[key] = time.time()
        logger.debug(f"[Cache] 设置缓存：{key}")

    def clear(self) -> None:
        """清空所有缓存"""
        self._cache.clear()
        self._timestamps.clear()
        logger.info("[Cache] 缓存已清空")

    def invalidate(self, key: str) -> None:
        """删除指定缓存"""
        if key in self._cache:
            del self._cache[key]
            del self._timestamps[key]
            logger.debug(f"[Cache] 删除缓存：{key}")


def cache_result(ttl: int | None = None):
    """缓存装饰器"""
    cache = CacheManager()

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"

            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result

            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl)

            return result

        return wrapper

    return decorator


weather_cache = CacheManager(default_ttl=600)
location_cache = CacheManager(default_ttl=3600)


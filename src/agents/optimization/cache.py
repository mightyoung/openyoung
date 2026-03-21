"""
Cache System - 缓存系统

提供结果缓存、模板缓存功能
"""

import hashlib
import json
import time
from dataclasses import dataclass, field
from functools import wraps
from typing import Any, Callable, Optional


@dataclass
class CacheEntry:
    """缓存条目"""

    key: str
    value: Any
    created_at: float = field(default_factory=time.time)
    expires_at: float = 0  # 0 = 永不过期
    hits: int = 0

    def is_expired(self) -> bool:
        """检查是否过期"""
        if self.expires_at == 0:
            return False
        return time.time() > self.expires_at


class Cache:
    """缓存"""

    def __init__(
        self,
        max_size: int = 1000,
        default_ttl: int = 3600,  # 秒
    ):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: dict[str, CacheEntry] = {}
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        entry = self._cache.get(key)
        if entry is None:
            self._misses += 1
            return None

        if entry.is_expired():
            del self._cache[key]
            self._misses += 1
            return None

        entry.hits += 1
        self._hits += 1
        return entry.value

    def set(self, key: str, value: Any, ttl: int = None):
        """设置缓存"""
        # 如果缓存已满，删除最旧的条目
        if len(self._cache) >= self.max_size:
            self._evict_oldest()

        ttl = ttl if ttl is not None else self.default_ttl
        expires_at = time.time() + ttl if ttl > 0 else 0

        self._cache[key] = CacheEntry(
            key=key,
            value=value,
            expires_at=expires_at,
        )

    def delete(self, key: str) -> bool:
        """删除缓存"""
        if key in self._cache:
            del self._cache[key]
            return True
        return False

    def clear(self):
        """清空缓存"""
        self._cache.clear()
        self._hits = 0
        self._misses = 0

    def _evict_oldest(self):
        """删除最旧的条目"""
        if not self._cache:
            return

        # 删除最少使用的
        oldest_key = min(
            self._cache.keys(), key=lambda k: (self._cache[k].hits, self._cache[k].created_at)
        )
        del self._cache[oldest_key]

    def get_stats(self) -> dict:
        """获取统计"""
        total = self._hits + self._misses
        hit_rate = self._hits / total if total > 0 else 0

        return {
            "size": len(self._cache),
            "max_size": self.max_size,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": hit_rate,
        }


# 全局缓存实例
_result_cache = Cache(max_size=500, default_ttl=1800)  # 30分钟
_template_cache = Cache(max_size=200, default_ttl=3600)  # 1小时


def cache_result(ttl: int = None, key_func: Callable = None):
    """缓存装饰器

    Args:
        ttl: 过期时间（秒）
        key_func: 自定义key函数，默认为函数名+参数hash
    """

    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # 生成缓存key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # 默认key生成
                key_data = f"{func.__name__}:{args}:{json.dumps(kwargs, sort_keys=True)}"
                cache_key = hashlib.md5(key_data.encode()).hexdigest()

            # 尝试从缓存获取
            cached = _result_cache.get(cache_key)
            if cached is not None:
                return cached

            # 执行函数
            result = await func(*args, **kwargs)

            # 存入缓存
            _result_cache.set(cache_key, result, ttl)

            return result

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # 生成缓存key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                key_data = f"{func.__name__}:{args}:{json.dumps(kwargs, sort_keys=True)}"
                cache_key = hashlib.md5(key_data.encode()).hexdigest()

            cached = _result_cache.get(cache_key)
            if cached is not None:
                return cached

            result = func(*args, **kwargs)
            _result_cache.set(cache_key, result, ttl)

            return result

        # 根据函数类型返回
        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def get_result_cache() -> Cache:
    """获取结果缓存"""
    return _result_cache


def get_template_cache() -> Cache:
    """获取模板缓存"""
    return _template_cache


class LRUCache:
    """LRU缓存实现"""

    def __init__(self, capacity: int = 100):
        self.capacity = capacity
        self._cache: dict[str, Any] = {}
        self._access_order: list[str] = []

    def get(self, key: str) -> Optional[Any]:
        """获取"""
        if key not in self._cache:
            return None

        # 更新访问顺序
        self._access_order.remove(key)
        self._access_order.append(key)

        return self._cache[key]

    def put(self, key: str, value: Any):
        """放入"""
        if key in self._cache:
            # 更新现有
            self._access_order.remove(key)
        elif len(self._cache) >= self.capacity:
            # 删除最旧的
            oldest = self._access_order.pop(0)
            del self._cache[oldest]

        self._cache[key] = value
        self._access_order.append(key)

    def clear(self):
        """清空"""
        self._cache.clear()
        self._access_order.clear()

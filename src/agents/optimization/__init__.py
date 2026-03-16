"""
Optimization Module - 性能优化模块

提供:
- Cache: 缓存系统
- Async Utilities: 异步工具
- Resource Manager: 资源管理
"""

from .async_utils import (
    AsyncPool,
    BatchResult,
    CircuitBreaker,
    RateLimiter,
    batch_execute,
    gather_with_limit,
    timeout_context,
)
from .cache import (
    Cache,
    LRUCache,
    cache_result,
    get_result_cache,
    get_template_cache,
)
from .resource_manager import (
    ConnectionPool,
    MemoryManager,
    ObjectPool,
    ResourceMonitor,
    get_resource_monitor,
    managed_resource,
)

__all__ = [
    # Cache
    "Cache",
    "LRUCache",
    "cache_result",
    "get_result_cache",
    "get_template_cache",
    # Async
    "batch_execute",
    "gather_with_limit",
    "timeout_context",
    "AsyncPool",
    "BatchResult",
    "CircuitBreaker",
    "RateLimiter",
    # Resource
    "ConnectionPool",
    "ObjectPool",
    "MemoryManager",
    "ResourceMonitor",
    "get_resource_monitor",
    "managed_resource",
]

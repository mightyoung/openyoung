"""
速率限制器

实现基于令牌桶算法的请求频率控制
"""

import threading
import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class RateLimitConfig:
    """速率限制配置"""

    requests_per_minute: int = 60
    requests_per_second: int = 10
    burst_size: int = 20


@dataclass
class RateLimitResult:
    """速率限制检查结果"""

    allowed: bool
    remaining_requests: int
    reset_time: float
    retry_after: Optional[float] = None


class TokenBucket:
    """令牌桶算法实现"""

    def __init__(self, capacity: int, refill_rate: float):
        """
        初始化令牌桶

        Args:
            capacity: 桶的容量（最大令牌数）
            refill_rate: 每秒补充的令牌数
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = float(capacity)
        self.last_refill = time.time()
        self._lock = threading.Lock()

    def consume(self, tokens: int = 1) -> bool:
        """
        尝试消费令牌

        Args:
            tokens: 要消费的令牌数

        Returns:
            是否成功消费
        """
        with self._lock:
            self._refill()

            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False

    def _refill(self) -> None:
        """补充令牌"""
        now = time.time()
        elapsed = now - self.last_refill

        # 计算应该补充的令牌数
        new_tokens = elapsed * self.refill_rate
        self.tokens = min(self.capacity, self.tokens + new_tokens)
        self.last_refill = now

    def get_remaining(self) -> int:
        """获取剩余令牌数"""
        with self._lock:
            self._refill()
            return int(self.tokens)

    def get_reset_time(self) -> float:
        """获取令牌桶重置时间（秒）"""
        with self._lock:
            self._refill()
            if self.tokens >= self.capacity:
                return 0.0
            # 如果 refill_rate 为 0，返回无穷大（永远不会补充）
            if self.refill_rate <= 0:
                return float("inf")
            # 计算充满所需时间
            return (self.capacity - self.tokens) / self.refill_rate


class RateLimiter:
    """速率限制器

    基于令牌桶算法实现多维度速率控制
    支持按 agent、ip、endpoint 等维度进行限制
    """

    def __init__(self, config: Optional[RateLimitConfig] = None):
        """
        初始化速率限制器

        Args:
            config: 速率限制配置
        """
        self.config = config or RateLimitConfig()

        # 按维度的令牌桶
        self._buckets: dict[str, TokenBucket] = {}
        self._lock = threading.Lock()

        # 全局限流
        self._global_bucket = TokenBucket(
            capacity=self.config.burst_size,
            refill_rate=self.config.requests_per_second,
        )

    def check(self, key: str, cost: int = 1) -> RateLimitResult:
        """
        检查请求是否允许

        Args:
            key: 限流维度标识（如 agent_id, ip 等）
            cost: 请求消耗的令牌数

        Returns:
            RateLimitResult: 检查结果
        """
        # 检查全局限制
        if not self._global_bucket.consume(cost):
            return RateLimitResult(
                allowed=False,
                remaining_requests=self._global_bucket.get_remaining(),
                reset_time=self._global_bucket.get_reset_time(),
                retry_after=self._global_bucket.get_reset_time(),
            )

        # 获取或创建维度的令牌桶
        bucket = self._get_bucket(key)

        if not bucket.consume(cost):
            return RateLimitResult(
                allowed=False,
                remaining_requests=bucket.get_remaining(),
                reset_time=bucket.get_reset_time(),
                retry_after=bucket.get_reset_time(),
            )

        return RateLimitResult(
            allowed=True,
            remaining_requests=bucket.get_remaining(),
            reset_time=bucket.get_reset_time(),
        )

    def _get_bucket(self, key: str) -> TokenBucket:
        """获取或创建令牌桶"""
        with self._lock:
            if key not in self._buckets:
                self._buckets[key] = TokenBucket(
                    capacity=self.config.burst_size,
                    refill_rate=self.config.requests_per_second,
                )
            return self._buckets[key]

    def reset(self, key: Optional[str] = None) -> None:
        """
        重置速率限制

        Args:
            key: 要重置的维度标识，None 表示重置所有
        """
        with self._lock:
            if key is None:
                self._buckets.clear()
                self._global_bucket = TokenBucket(
                    capacity=self.config.burst_size,
                    refill_rate=self.config.requests_per_second,
                )
            elif key in self._buckets:
                del self._buckets[key]

    def get_status(self, key: str) -> dict:
        """
        获取速率限制状态

        Args:
            key: 维度标识

        Returns:
            状态信息字典
        """
        bucket = self._get_bucket(key)
        return {
            "key": key,
            "remaining": bucket.get_remaining(),
            "reset_time": bucket.get_reset_time(),
            "capacity": bucket.capacity,
            "refill_rate": bucket.refill_rate,
        }


# ========== Convenience Functions ==========


def create_rate_limiter(
    requests_per_minute: int = 60,
    requests_per_second: int = 10,
    burst_size: int = 20,
) -> RateLimiter:
    """
    便捷函数：创建速率限制器

    Args:
        requests_per_minute: 每分钟请求数
        requests_per_second: 每秒请求数
        burst_size: 突发大小

    Returns:
        RateLimiter 实例
    """
    config = RateLimitConfig(
        requests_per_minute=requests_per_minute,
        requests_per_second=requests_per_second,
        burst_size=burst_size,
    )
    return RateLimiter(config)

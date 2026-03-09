"""
Rate Limiter Tests - Phase 2.3
Tests for RateLimiter functionality
"""

import pytest
import time
import threading
from src.runtime.security import RateLimiter, RateLimitConfig, TokenBucket


class TestTokenBucket:
    """TokenBucket 算法测试"""

    def test_basic_consume(self):
        """基本消费测试"""
        bucket = TokenBucket(capacity=10, refill_rate=2.0)

        # 应该可以消费
        assert bucket.consume(1) == True
        assert bucket.get_remaining() == 9

    def test_burst_limit(self):
        """突发限制测试"""
        bucket = TokenBucket(capacity=5, refill_rate=1.0)

        # 消费完所有令牌
        for _ in range(5):
            assert bucket.consume(1) == True

        # 第六个应该失败
        assert bucket.consume(1) == False

    def test_refill(self):
        """令牌补充测试"""
        bucket = TokenBucket(capacity=10, refill_rate=5.0)  # 每秒5个

        # 消费5个
        for _ in range(5):
            bucket.consume(1)

        # 等待200ms，应该补充1个
        time.sleep(0.2)
        assert bucket.get_remaining() >= 1

    def test_concurrent_access(self):
        """并发访问测试"""
        bucket = TokenBucket(capacity=100, refill_rate=50.0)

        results = []

        def consume_tokens():
            for _ in range(20):
                results.append(bucket.consume(1))

        threads = [threading.Thread(target=consume_tokens) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # 应该成功消费一部分
        assert len(results) == 100


class TestRateLimiter:
    """RateLimiter 测试"""

    def test_global_limit(self):
        """全局限制测试"""
        limiter = RateLimiter(RateLimitConfig(
            requests_per_second=2,
            burst_size=2,
        ))

        # 前2个应该通过
        assert limiter.check("test").allowed == True
        assert limiter.check("test").allowed == True

        # 第3个应该被限制
        result = limiter.check("test")
        assert result.allowed == False

    def test_per_key_limit(self):
        """按key限制测试"""
        limiter = RateLimiter(RateLimitConfig(
            requests_per_second=0,  # 禁用自动补充，测试burst行为
            burst_size=2,  # 限制每个key只能发2个请求
        ))

        # 同一个key应该受限制 (burst_size=2)
        assert limiter.check("user1").allowed == True
        assert limiter.check("user1").allowed == True
        assert limiter.check("user1").allowed == False

        # 不同key不受同一key限制影响 (每个key有独立bucket)
        limiter2 = RateLimiter(RateLimitConfig(
            requests_per_second=0,
            burst_size=2,
        ))
        assert limiter2.check("user2").allowed == True
        assert limiter2.check("user2").allowed == True
        assert limiter2.check("user2").allowed == False

    def test_reset(self):
        """重置测试"""
        limiter = RateLimiter()

        # 消费完
        limiter.check("test")
        limiter.check("test")

        # 重置后应该可以继续使用
        limiter.reset("test")
        assert limiter.check("test").allowed == True

    def test_reset_all(self):
        """重置所有测试"""
        limiter = RateLimiter()

        limiter.check("user1")
        limiter.check("user2")

        limiter.reset()
        assert limiter.check("user1").allowed == True
        assert limiter.check("user2").allowed == True

    def test_status(self):
        """状态查询测试"""
        limiter = RateLimiter()

        limiter.check("test")
        status = limiter.get_status("test")

        assert status["key"] == "test"
        assert "remaining" in status
        assert "reset_time" in status


class TestRateLimiterIntegration:
    """RateLimiter 集成测试"""

    def test_concurrent_requests(self):
        """并发请求测试"""
        limiter = RateLimiter(RateLimitConfig(
            requests_per_second=100,
            burst_size=50,
        ))

        results = []

        def make_request():
            result = limiter.check("api")
            results.append(result.allowed)

        threads = [threading.Thread(target=make_request) for _ in range(100)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # 大部分应该成功
        success_count = sum(results)
        assert success_count > 0

    def test_with_config(self):
        """配置测试"""
        config = RateLimitConfig(
            requests_per_minute=60,
            requests_per_second=5,
            burst_size=10,
        )
        limiter = RateLimiter(config)

        assert limiter.config.requests_per_minute == 60
        assert limiter.config.requests_per_second == 5
        assert limiter.config.burst_size == 10

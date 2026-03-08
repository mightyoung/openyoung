"""
TokenTracker Tests
"""

import os
import tempfile

import pytest

from src.datacenter.token_tracker import MODEL_PRICING, TokenTracker


@pytest.fixture
def tracker():
    """创建临时 TokenTracker"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test_tokens.db")
        yield TokenTracker(db_path)


class TestTokenTracker:
    """TokenTracker 测试"""

    def test_record_token_usage(self, tracker):
        """测试记录 token 使用"""
        token_id = tracker.record(
            run_id="run_001",
            model="deepseek-chat",
            provider="deepseek",
            input_tokens=1000,
            output_tokens=500,
            latency_ms=1500
        )

        assert token_id is not None
        assert token_id.startswith("tok_")

    def test_get_by_run(self, tracker):
        """测试获取 Run 的 token 记录"""
        run_id = "run_002"

        # 记录多条
        tracker.record(
            run_id=run_id,
            model="deepseek-chat",
            provider="deepseek",
            input_tokens=1000,
            output_tokens=500
        )
        tracker.record(
            run_id=run_id,
            model="gpt-4o",
            provider="openai",
            input_tokens=2000,
            output_tokens=1000
        )

        records = tracker.get_by_run(run_id)
        assert len(records) == 2

    def test_get_summary(self, tracker):
        """测试获取摘要"""
        run_id = "run_003"

        tracker.record(
            run_id=run_id,
            model="deepseek-chat",
            provider="deepseek",
            input_tokens=1000,
            output_tokens=500
        )
        tracker.record(
            run_id=run_id,
            model="deepseek-chat",
            provider="deepseek",
            input_tokens=500,
            output_tokens=250
        )

        summary = tracker.get_summary(run_id)
        assert summary["total_calls"] == 2
        assert summary["total_input_tokens"] == 1500
        assert summary["total_output_tokens"] == 750

    def test_cost_calculation(self, tracker):
        """测试成本计算"""
        # DeepSeek: input $0.27/M, output $1.1/M
        token_id = tracker.record(
            run_id="run_004",
            model="deepseek-chat",
            provider="deepseek",
            input_tokens=1_000_000,  # 1M input
            output_tokens=1_000_000   # 1M output
        )

        records = tracker.get_by_run("run_004")
        # 1M * 0.27/1M + 1M * 1.1/1M = 0.27 + 1.1 = 1.37
        assert abs(records[0]["cost"] - 1.37) < 0.01

    def test_budget_check(self, tracker):
        """测试预算检查"""
        run_id = "run_005"

        tracker.record(
            run_id=run_id,
            model="deepseek-chat",
            provider="deepseek",
            input_tokens=1_000_000,
            output_tokens=500_000
        )

        # 预算充足
        result = tracker.check_budget(run_id=run_id, budget_usd=10.0)
        assert result["within_budget"] is True

        # 预算不足
        result = tracker.check_budget(run_id=run_id, budget_usd=0.5)
        assert result["within_budget"] is False
        assert result["over_budget_usd"] > 0

    def test_model_pricing(self, tracker):
        """测试模型定价"""
        # 测试已知的模型定价
        assert MODEL_PRICING["deepseek-chat"]["input"] == 0.27
        assert MODEL_PRICING["deepseek-chat"]["output"] == 1.1

        assert MODEL_PRICING["gpt-4o"]["input"] == 2.5
        assert MODEL_PRICING["gpt-4o"]["output"] == 10.0

        # 测试默认定价
        price = tracker._get_model_price("unknown-model")
        assert price == MODEL_PRICING["default"]

    def test_get_by_model(self, tracker):
        """测试按模型统计"""
        run_id = "run_006"

        tracker.record(
            run_id=run_id,
            model="deepseek-chat",
            provider="deepseek",
            input_tokens=1000,
            output_tokens=500
        )
        tracker.record(
            run_id=run_id,
            model="deepseek-chat",
            provider="deepseek",
            input_tokens=2000,
            output_tokens=1000
        )
        tracker.record(
            run_id=run_id,
            model="gpt-4o",
            provider="openai",
            input_tokens=500,
            output_tokens=250
        )

        by_model = tracker.get_by_model(run_id)
        assert len(by_model) == 2

        # 验证按 cost 排序
        costs = [m["total_cost"] for m in by_model]
        assert costs == sorted(costs, reverse=True)

    def test_delete_by_run(self, tracker):
        """测试删除 Run 的记录"""
        run_id = "run_007"

        tracker.record(
            run_id=run_id,
            model="deepseek-chat",
            provider="deepseek",
            input_tokens=1000,
            output_tokens=500
        )

        records = tracker.get_by_run(run_id)
        assert len(records) == 1

        tracker.delete_by_run(run_id)

        records = tracker.get_by_run(run_id)
        assert len(records) == 0

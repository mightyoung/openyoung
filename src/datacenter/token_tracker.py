"""
TokenTracker - Token 使用追踪
记录 LLM 调用级别的 token 使用情况
使用 BaseStorage 基类
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from .base_storage import BaseStorage

# 模型定价（单位：每 1M tokens）
# 参考 2024 年主流 LLM pricing
MODEL_PRICING = {
    # OpenAI
    "gpt-4o": {"input": 2.5, "output": 10.0},
    "gpt-4o-mini": {"input": 0.15, "output": 0.6},
    "gpt-4-turbo": {"input": 10.0, "output": 30.0},
    "gpt-4": {"input": 30.0, "output": 60.0},
    "gpt-3.5-turbo": {"input": 0.5, "output": 1.5},
    # Anthropic
    "claude-3-5-sonnet": {"input": 3.0, "output": 15.0},
    "claude-3-opus": {"input": 15.0, "output": 75.0},
    "claude-3-sonnet": {"input": 3.0, "output": 15.0},
    "claude-3-haiku": {"input": 0.25, "output": 1.25},
    # DeepSeek
    "deepseek-chat": {"input": 0.27, "output": 1.1},
    "deepseek-coder": {"input": 0.27, "output": 1.1},
    "deepseek-reasoner": {"input": 0.68, "output": 2.69},
    # 默认定价
    "default": {"input": 1.0, "output": 3.0},
}


@dataclass
class TokenRecord:
    """Token 使用记录"""
    token_id: str
    run_id: str
    step_id: str | None
    model: str
    provider: str
    input_tokens: int
    output_tokens: int
    reasoning_tokens: int = 0  # 推理 token (如 deepseek-reasoner)
    cost: float = 0.0  # 美元
    latency_ms: int = 0
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)


class TokenTracker(BaseStorage):
    """Token 使用追踪器"""

    def __init__(self, db_path: str = ".young/tokens.db"):
        super().__init__(db_path)

    def _init_db(self) -> None:
        """初始化数据库表结构"""
        self._create_table(
            "tokens",
            {
                "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
                "token_id": "TEXT NOT NULL UNIQUE",
                "run_id": "TEXT NOT NULL",
                "step_id": "TEXT",
                "model": "TEXT NOT NULL",
                "provider": "TEXT NOT NULL",
                "input_tokens": "INTEGER DEFAULT 0",
                "output_tokens": "INTEGER DEFAULT 0",
                "reasoning_tokens": "INTEGER DEFAULT 0",
                "cost": "REAL DEFAULT 0.0",
                "latency_ms": "INTEGER DEFAULT 0",
                "timestamp": "TEXT NOT NULL",
                "metadata": "TEXT",
                "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
            },
            indexes=[
                ("idx_run", "run_id"),
                ("idx_step", "step_id"),
                ("idx_model", "model"),
                ("idx_timestamp", "timestamp")
            ]
        )

    def _get_model_price(self, model: str) -> dict:
        """获取模型定价"""
        # 精确匹配
        if model in MODEL_PRICING:
            return MODEL_PRICING[model]
        # 前缀匹配
        for prefix, price in MODEL_PRICING.items():
            if model.startswith(prefix):
                return price
        # 默认定价
        return MODEL_PRICING["default"]

    def _calculate_cost(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
        reasoning_tokens: int = 0
    ) -> float:
        """计算调用成本（美元）"""
        price = self._get_model_price(model)
        input_cost = (input_tokens / 1_000_000) * price["input"]
        output_cost = (output_tokens / 1_000_000) * price["output"]
        reasoning_cost = (reasoning_tokens / 1_000_000) * price.get("input", price["output"])
        return round(input_cost + output_cost + reasoning_cost, 6)

    def record(
        self,
        run_id: str,
        model: str,
        provider: str,
        input_tokens: int,
        output_tokens: int,
        step_id: str = None,
        reasoning_tokens: int = 0,
        latency_ms: int = 0,
        metadata: dict = None
    ) -> str:
        """记录一次 LLM 调用的 token 使用

        Args:
            run_id: Run ID
            model: 模型名
            provider: 提供商 (openai/anthropic/deepseek)
            input_tokens: 输入 token 数
            output_tokens: 输出 token 数
            step_id: Step ID (可选)
            reasoning_tokens: 推理 token 数
            latency_ms: 延迟（毫秒）
            metadata: 额外元数据

        Returns:
            token_id
        """
        # 输入验证
        if not run_id or not run_id.strip():
            raise ValueError("run_id cannot be empty")
        if not model or not model.strip():
            raise ValueError("model cannot be empty")
        if input_tokens < 0:
            raise ValueError("input_tokens must be non-negative")
        if output_tokens < 0:
            raise ValueError("output_tokens must be non-negative")

        token_id = f"tok_{uuid.uuid4().hex[:12]}"
        cost = self._calculate_cost(model, input_tokens, output_tokens, reasoning_tokens)

        self._execute(
            """
            INSERT INTO tokens
            (token_id, run_id, step_id, model, provider, input_tokens, output_tokens,
             reasoning_tokens, cost, latency_ms, timestamp, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                token_id,
                run_id,
                step_id,
                model,
                provider,
                input_tokens,
                output_tokens,
                reasoning_tokens,
                cost,
                latency_ms,
                datetime.now().isoformat(),
                self._json_serialize(metadata or {})
            )
        )

        return token_id

    def get_by_run(self, run_id: str) -> list[dict]:
        """获取某个 Run 的所有 token 记录

        Args:
            run_id: Run ID

        Returns:
            token 记录列表
        """
        if not run_id:
            raise ValueError("run_id cannot be empty")

        return self._execute(
            "SELECT * FROM tokens WHERE run_id = ? ORDER BY timestamp ASC",
            (run_id,),
            fetch=True
        ) or []

    def get_by_step(self, step_id: str) -> list[dict]:
        """获取某个 Step 的 token 记录

        Args:
            step_id: Step ID

        Returns:
            token 记录列表
        """
        if not step_id:
            raise ValueError("step_id cannot be empty")

        return self._execute(
            "SELECT * FROM tokens WHERE step_id = ? ORDER BY timestamp ASC",
            (step_id,),
            fetch=True
        ) or []

    def get_summary(self, run_id: str = None) -> dict:
        """获取 token 使用摘要

        Args:
            run_id: Run ID (可选，不提供则返回全局)

        Returns:
            摘要字典
        """
        if run_id:
            where_clause = "WHERE run_id = ?"
            params = (run_id,)
        else:
            where_clause = ""
            params = None

        # 总计
        total = self._execute(
            f"""
            SELECT
                COUNT(*) as total_calls,
                COALESCE(SUM(input_tokens), 0) as total_input,
                COALESCE(SUM(output_tokens), 0) as total_output,
                COALESCE(SUM(reasoning_tokens), 0) as total_reasoning,
                COALESCE(SUM(cost), 0) as total_cost,
                COALESCE(AVG(latency_ms), 0) as avg_latency
            FROM tokens
            {where_clause}
            """,
            params,
            fetch=True
        )

        if not total or total[0]["total_calls"] == 0:
            return {
                "total_calls": 0,
                "total_input_tokens": 0,
                "total_output_tokens": 0,
                "total_reasoning_tokens": 0,
                "total_cost_usd": 0.0,
                "avg_latency_ms": 0
            }

        row = total[0]
        return {
            "total_calls": row["total_calls"],
            "total_input_tokens": row["total_input"],
            "total_output_tokens": row["total_output"],
            "total_reasoning_tokens": row["total_reasoning"],
            "total_cost_usd": round(row["total_cost"], 6),
            "avg_latency_ms": round(row["avg_latency"], 2)
        }

    def get_by_model(self, run_id: str = None) -> list[dict]:
        """按模型统计 token 使用

        Args:
            run_id: Run ID (可选)

        Returns:
            按模型的统计列表
        """
        if run_id:
            where_clause = "WHERE run_id = ?"
            params = (run_id,)
        else:
            where_clause = ""
            params = None

        return self._execute(
            f"""
            SELECT
                model,
                provider,
                COUNT(*) as call_count,
                SUM(input_tokens) as total_input,
                SUM(output_tokens) as total_output,
                SUM(cost) as total_cost
            FROM tokens
            {where_clause}
            GROUP BY model
            ORDER BY total_cost DESC
            """,
            params,
            fetch=True
        ) or []

    def check_budget(
        self,
        run_id: str = None,
        budget_usd: float = None,
        budget_tokens: int = None
    ) -> dict:
        """检查是否超出预算

        Args:
            run_id: Run ID (可选)
            budget_usd: 预算（美元）
            budget_tokens: 预算（token 数）

        Returns:
            预算检查结果
        """
        summary = self.get_summary(run_id)

        result = {
            "within_budget": True,
            "total_cost_usd": summary["total_cost_usd"],
            "total_tokens": (
                summary["total_input_tokens"] +
                summary["total_output_tokens"] +
                summary["total_reasoning_tokens"]
            ),
            "budget_usd": budget_usd,
            "budget_tokens": budget_tokens
        }

        if budget_usd is not None and summary["total_cost_usd"] > budget_usd:
            result["within_budget"] = False
            result["over_budget_usd"] = summary["total_cost_usd"] - budget_usd

        if budget_tokens is not None:
            if result["total_tokens"] > budget_tokens:
                result["within_budget"] = False
                result["over_budget_tokens"] = result["total_tokens"] - budget_tokens

        return result

    def get_trend(self, days: int = 7) -> list[dict]:
        """获取每日 token 使用趋势

        Args:
            days: 天数

        Returns:
            每日统计列表
        """
        return self._execute(
            """
            SELECT
                DATE(timestamp) as date,
                COUNT(*) as call_count,
                SUM(input_tokens) as total_input,
                SUM(output_tokens) as total_output,
                SUM(cost) as total_cost
            FROM tokens
            WHERE timestamp >= datetime('now', ?)
            GROUP BY DATE(timestamp)
            ORDER BY date ASC
            """,
            (f"-{days} days",),
            fetch=True
        ) or []

    def delete_by_run(self, run_id: str) -> int:
        """删除某个 Run 的所有 token 记录

        Args:
            run_id: Run ID

        Returns:
            删除的记录数
        """
        if not run_id:
            raise ValueError("run_id cannot be empty")

        cursor = self._execute(
            "DELETE FROM tokens WHERE run_id = ?",
            (run_id,),
            fetch=False
        )
        # 返回受影响的行数需要特殊处理
        result = self._execute(
            "SELECT changes() as cnt",
            fetch=True
        )
        return result[0]["cnt"] if result else 0


def get_token_tracker(db_path: str = ".young/tokens.db") -> TokenTracker:
    """获取 TokenTracker 实例（便捷函数）"""
    return TokenTracker(db_path)

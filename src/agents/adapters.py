"""
Agent Adapters - 将不同 Agent 接口适配到 EvalRunner

用于将 SubAgent 等返回 str 的 Agent 适配为 EvalRunner 期望的
dict {transcript, outcome, metrics} 接口
"""

from typing import Any, Protocol

from src.core.types import Task


class EvalAgent(Protocol):
    """EvalRunner 期望的 Agent 接口"""

    async def run(self, prompt: str) -> dict[str, Any] | str:
        """执行任务

        Returns:
            - dict: {transcript: list, outcome: dict, metrics: dict}
            - str: 简化的结果字符串
        """
        ...


class AgentAdapter:
    """将 SubAgent 适配到 EvalRunner 接口

    SubAgent.run(task, context) -> str
    =>
    AgentAdapter.run(prompt) -> {transcript, outcome, metrics}
    """

    def __init__(self, sub_agent: Any):
        """初始化适配器

        Args:
            sub_agent: SubAgent 实例
        """
        self._agent = sub_agent

    async def run(self, prompt: str) -> dict[str, Any]:
        """执行 SubAgent 并转换为 EvalRunner 格式

        Args:
            prompt: 任务提示词

        Returns:
            dict: {
                transcript: [...],  # 执行轨迹
                outcome: {...},     # 最终结果
                metrics: {...}      # 执行指标
            }
        """
        # 构建 Task 对象
        task = Task(id=f"eval_{id(self)}", input=prompt)

        # 执行 SubAgent (返回 str)
        result = await self._agent.run(task, context={})

        # 转换为 EvalRunner 格式
        return self._adapt_result(result)

    def _adapt_result(self, result: str) -> dict[str, Any]:
        """将 str 结果适配为 dict 格式

        Args:
            result: SubAgent 返回的字符串

        Returns:
            dict: {transcript, outcome, metrics}
        """
        # 尝试解析 JSON
        import json

        try:
            parsed = json.loads(result)
            if isinstance(parsed, dict):
                return {
                    "transcript": parsed.get("transcript", []),
                    "outcome": parsed.get("outcome", parsed),
                    "metrics": parsed.get("metrics", {}),
                }
        except (json.JSONDecodeError, TypeError):
            pass

        # 默认：把字符串包装为 outcome
        return {
            "transcript": [{"role": "assistant", "content": result}],
            "outcome": {"result": result},
            "metrics": {
                "num_turns": 1,
            },
        }


def adapt_subagent(sub_agent: Any) -> AgentAdapter:
    """将 SubAgent 包装为 EvalRunner 兼容的适配器

    Args:
        sub_agent: SubAgent 实例

    Returns:
        AgentAdapter: 适配后的 Agent
    """
    return AgentAdapter(sub_agent)

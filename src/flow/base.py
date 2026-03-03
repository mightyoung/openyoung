"""
FlowSkill - 工作流编排基类
对标 OpenCode，实现 Flow Skill 机制
"""

from abc import ABC, abstractmethod
from typing import Optional


class FlowSkill(ABC):
    """Flow Skill - 控制 Agent 工作流编排

    核心接口：
    - pre_process: 前置处理（用户输入到达 Agent 前）
    - post_process: 后置处理（Agent 输出返回前）
    - should_delegate: 判断是否需要委托给 SubAgent
    - get_subagent_type: 获取合适的 SubAgent 类型
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Flow Skill 名称"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Flow Skill 描述"""
        pass

    @property
    def trigger_patterns(self) -> list[str]:
        """触发模式"""
        return []

    @abstractmethod
    async def pre_process(self, user_input: str, context: dict) -> str:
        """前置处理 - 用户输入到达 Agent 前调用

        Args:
            user_input: 用户输入
            context: 上下文字典

        Returns:
            处理后的输入
        """
        pass

    @abstractmethod
    async def post_process(self, agent_output: str, context: dict) -> str:
        """后置处理 - Agent 输出返回前调用

        Args:
            agent_output: Agent 输出
            context: 上下文字典

        Returns:
            处理后的输出
        """
        pass

    async def should_delegate(self, task: str, context: dict) -> bool:
        """判断是否需要委托给 SubAgent

        默认不委托，子类可以重写
        """
        return False

    async def get_subagent_type(self, task: str) -> Optional[str]:
        """获取合适的 SubAgent 类型

        默认返回 None，子类可以重写
        """
        return None

    def _decompose(self, user_input: str) -> list[str]:
        """分解任务为步骤（默认实现）"""
        # 简单按行分解
        lines = [l.strip() for l in user_input.split("\n") if l.strip()]
        return lines if lines else [user_input]

    def _identify_parallel_tasks(self, user_input: str) -> list[str]:
        """识别可并行的子任务（默认实现）"""
        # 简单按关键词识别
        return [user_input]

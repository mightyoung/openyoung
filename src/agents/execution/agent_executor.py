"""
Agent Executor Client - Agent 执行器封装

提取自 young_agent.py 的执行逻辑。
提供简化的 Agent 执行接口。
"""

import re
import uuid

from src.core.types import Message, SubAgentType, Task


class AgentExecutorClient:
    """Agent 执行器客户端封装

    提供简化的 Agent 执行接口，
    包含 SubAgent 委托和 LLM 调用逻辑。
    """

    def __init__(
        self,
        llm_client=None,
        tool_executor=None,
        config=None,
        max_tool_calls: int = 10,
    ):
        """初始化 AgentExecutorClient

        Args:
            llm_client: LLM 客户端
            tool_executor: 工具执行器
            config: Agent 配置
            max_tool_calls: 最大工具调用次数
        """
        self._llm = llm_client
        self._tool_executor = tool_executor
        self._config = config
        self._max_tool_calls = max_tool_calls
        self._history: list[Message] = []

    def set_history(self, history: list) -> None:
        """设置历史消息"""
        self._history = history

    async def parse_input(self, user_input: str) -> Task:
        """解析用户输入 - 支持 @mention 触发 SubAgent"""
        # 参考 Claude Code Task 协议: @subagent task_description
        match = re.match(r"@(\w+)\s+(.+)", user_input.strip())
        if match:
            subagent_name = match.group(1)
            description = match.group(2)

            # 查找对应的 SubAgentType
            subagent_type = None

            # 首先检查是否匹配预定义类型
            for sat in SubAgentType:
                if sat.value == subagent_name:
                    subagent_type = sat
                    break

            # 如果没有匹配预定义类型，检查是否在已加载的 SubAgents 中
            if subagent_type is None:
                # 使用 GENERAL 类型作为占位符
                subagent_type = SubAgentType.GENERAL

            return Task(
                id=str(uuid.uuid4()),
                description=description,
                input=description,
                subagent_type=subagent_type,
                custom_subagent=subagent_name,
            )
        return Task(id=str(uuid.uuid4()), description=user_input, input=user_input)

    async def execute_task(self, task: Task) -> str:
        """执行任务核心逻辑（已迁移到 task_executor.py，此处保留接口）"""
        # 此方法保留用于向后兼容，实际执行已移至 task_executor.py
        from src.agents.task_executor import TaskExecutor

        executor = TaskExecutor(
            tool_executor=self._tool_executor,
            config=self._config,
            max_tool_calls=self._max_tool_calls,
        )
        executor.set_history(self._history)
        return await executor.execute(task)

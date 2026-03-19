"""
Tool Executor Client - ToolExecutor 工具执行器封装

提取自 young_agent.py 对 ToolExecutor 的使用。
提供简化的 ToolExecutor 客户端接口。
"""

from src.tools.executor import ToolExecutor


class ToolExecutorClient:
    """ToolExecutor 客户端封装

    提供简化的工具执行接口。
    """

    def __init__(self, tool_executor: ToolExecutor = None):
        """初始化 ToolExecutorClient

        Args:
            tool_executor: ToolExecutor 实例
        """
        self._executor = tool_executor

    def set_executor(self, executor: ToolExecutor) -> None:
        """设置 ToolExecutor 实例"""
        self._executor = executor

    def get_tool_schemas(self) -> list[dict]:
        """获取工具 schema 列表"""
        if self._executor:
            return self._executor.get_tool_schemas()
        return []

    async def execute(self, tool_name: str, arguments: dict):
        """执行工具

        Args:
            tool_name: 工具名称
            arguments: 工具参数

        Returns:
            工具执行结果
        """
        if self._executor:
            return await self._executor.execute(tool_name, arguments)
        return None

    def set_sandbox(self, sandbox) -> None:
        """设置沙箱"""
        if self._executor:
            self._executor.set_sandbox(sandbox)

    def set_sandbox_pool(self, pool) -> None:
        """设置沙箱池"""
        if self._executor:
            self._executor.set_sandbox_pool(pool)

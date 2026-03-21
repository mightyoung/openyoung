"""
LangGraph 统一工具接口

实现 LangGraph 兼容的工具抽象，统一现有工具系统
参考: LangChain BaseTool 规范
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional, Type

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class ToolResultStatus(str, Enum):
    """工具执行结果状态"""

    SUCCESS = "success"
    ERROR = "error"
    PARTIAL = "partial"


@dataclass
class ToolResult:
    """工具执行结果"""

    status: ToolResultStatus
    data: dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    message: str = ""
    execution_time_ms: float = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    def is_success(self) -> bool:
        return self.status == ToolResultStatus.SUCCESS

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "data": self.data,
            "error": self.error,
            "message": self.message,
            "execution_time_ms": self.execution_time_ms,
            "metadata": self.metadata,
        }


class BaseTool(ABC):
    """基础工具抽象 - LangGraph/LangChain 兼容

    提供统一的工具接口，支持:
    - 同步/异步执行
    - 参数验证
    - 执行历史记录
    - 错误处理
    """

    name: str
    description: str
    args_schema: Type[BaseModel]

    def __init__(self):
        self._execution_history: list[dict[str, Any]] = []

    @abstractmethod
    async def execute(self, input: dict[str, Any]) -> ToolResult:
        """执行工具

        Args:
            input: 工具输入参数

        Returns:
            ToolResult: 执行结果
        """
        pass

    def validate_input(self, input: dict[str, Any]) -> tuple[bool, Optional[str]]:
        """验证输入参数

        Args:
            input: 输入参数

        Returns:
            (is_valid, error_message)
        """
        try:
            # 使用 Pydantic 验证
            self.args_schema(**input)
            return True, None
        except Exception as e:
            return False, str(e)

    async def run(self, input: dict[str, Any]) -> ToolResult:
        """运行工具 (带验证和错误处理)"""
        import time

        start_time = time.time()

        # 验证输入
        is_valid, error_msg = self.validate_input(input)
        if not is_valid:
            return ToolResult(
                status=ToolResultStatus.ERROR,
                error=error_msg,
                message=f"Input validation failed: {error_msg}",
                execution_time_ms=(time.time() - start_time) * 1000,
            )

        # 执行
        try:
            result = await self.execute(input)
            result.execution_time_ms = (time.time() - start_time) * 1000

            # 记录历史
            self._execution_history.append(
                {
                    "timestamp": datetime.now().isoformat(),
                    "input": input,
                    "result": result.to_dict(),
                }
            )

            return result

        except Exception as e:
            logger.error(f"Tool execution error in {self.name}: {e}")
            return ToolResult(
                status=ToolResultStatus.ERROR,
                error=str(e),
                message=f"Tool execution failed: {str(e)}",
                execution_time_ms=(time.time() - start_time) * 1000,
            )

    def get_execution_history(self) -> list[dict[str, Any]]:
        """获取执行历史"""
        return self._execution_history.copy()

    def clear_history(self):
        """清空执行历史"""
        self._execution_history.clear()

    def to_langchain_tool(self):
        """转换为 LangChain Tool

        用于 LangGraph 集成
        """
        from langchain_core.tools import BaseTool as LangChainBaseTool

        # 创建动态工具类
        tool_instance = self

        class DynamicLangChainTool(LangChainBaseTool):
            name: str = tool_instance.name
            description: str = tool_instance.description
            args_schema: Type[BaseModel] = tool_instance.args_schema

            async def _arun(self, input: str | dict) -> str:
                if isinstance(input, str):
                    # 尝试解析 JSON
                    import json

                    try:
                        input_dict = json.loads(input)
                    except json.JSONDecodeError:
                        input_dict = {"query": input}
                else:
                    input_dict = input

                result = await tool_instance.run(input_dict)
                return result.message or str(result.data)

            def _run(self, input: str | dict) -> str:
                import asyncio

                if isinstance(input, str):
                    import json

                    try:
                        input_dict = json.loads(input)
                    except json.JSONDecodeError:
                        input_dict = {"query": input}
                else:
                    input_dict = input

                # 同步版本 (简化)
                return asyncio.run(self._arun(input_dict))

        return DynamicLangChainTool()


@dataclass
class ToolContract:
    """工具契约 - 定义工具的能力和限制"""

    name: str
    version: str = "1.0.0"
    capabilities: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    rate_limit: Optional[dict[str, int]] = None
    timeout_seconds: int = 60
    retry_enabled: bool = True
    max_retries: int = 3


class ToolRegistry:
    """工具注册表 - 管理所有可用工具

    类似 Claude Code Tools 系统
    """

    def __init__(self):
        self._tools: dict[str, BaseTool] = {}
        self._contracts: dict[str, ToolContract] = {}
        self._aliases: dict[str, str] = {}  # alias -> tool_name

    def register(self, tool: BaseTool, contract: Optional[ToolContract] = None) -> None:
        """注册工具"""
        self._tools[tool.name] = tool
        if contract:
            self._contracts[tool.name] = contract
        logger.info(f"Registered tool: {tool.name}")

    def register_alias(self, alias: str, tool_name: str) -> None:
        """注册工具别名"""
        self._aliases[alias] = tool_name

    def get(self, name: str) -> Optional[BaseTool]:
        """获取工具"""
        # 先检查别名
        tool_name = self._aliases.get(name, name)
        return self._tools.get(tool_name)

    def list_tools(self) -> list[str]:
        """列出所有工具"""
        return list(self._tools.keys())

    def get_contract(self, tool_name: str) -> Optional[ToolContract]:
        """获取工具契约"""
        return self._contracts.get(tool_name)

    def unregister(self, name: str) -> bool:
        """注销工具"""
        if name in self._tools:
            del self._tools[name]
            if name in self._contracts:
                del self._contracts[name]
            return True
        return False


# 全局工具注册表
_tool_registry = ToolRegistry()


def get_tool_registry() -> ToolRegistry:
    """获取全局工具注册表"""
    return _tool_registry


def register_tool(tool: BaseTool, contract: Optional[ToolContract] = None) -> None:
    """便捷函数: 注册工具"""
    _tool_registry.register(tool, contract)


# ====================
# 便捷工具创建装饰器
# ====================


def tool(
    name: str,
    description: str,
    args_schema: Type[BaseModel] | None = None,
):
    """装饰器: 创建工具

    Usage:
        @tool(name="web_search", description="Search the web")
        class WebSearchTool(BaseTool):
            async def execute(self, input: dict) -> ToolResult:
                ...
    """

    class WrapperTool(BaseTool):
        name = name
        description = description
        args_schema = args_schema or BaseModel

        def __init__(self, original_class):
            super().__init__()
            self._original = original_class()
            self.execute = self._original.execute

        async def execute(self, input: dict[str, Any]) -> ToolResult:
            return await self._original.execute(input)

    def decorator(cls):
        return WrapperTool(cls)

    return decorator


# ====================
# LangGraph 工具适配器
# ====================


class LangGraphToolAdapter:
    """LangGraph 工具适配器

    将现有工具适配为 LangGraph 可用格式
    """

    def __init__(self, tool: BaseTool):
        self.tool = tool

    def to_langgraph_format(self) -> dict[str, Any]:
        """转换为 LangGraph 格式"""
        return {
            "name": self.tool.name,
            "description": self.tool.description,
            "args_schema": self.tool.args_schema,
        }

    async def execute(self, input: dict[str, Any]) -> dict[str, Any]:
        """执行并返回 LangGraph 兼容格式"""
        result = await self.tool.run(input)
        return result.to_dict()

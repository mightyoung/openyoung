"""
Agent Mixins - Agent 混合类

提供可组合的 Agent 功能，用于渐进式重构:
- AgentToolsMixin: 工具管理
- AgentMemoryMixin: 记忆管理
- AgentHooksMixin: Hooks 管理

设计原则:
- 使用组合而非继承
- 保持向后兼容
- 逐步迁移到 BaseAgent 架构
"""

from typing import Any, Callable, Optional


class AgentToolsMixin:
    """Agent 工具管理混合类

    提供与 BaseAgent 兼容的工具管理功能:
    - 工具注册/注销
    - 工具调用
    - 工具列表
    """

    def __init__(self):
        self._tools: dict[str, Any] = {}
        self._tool_schemas: list[dict] = []

    def register_tool(self, name: str, func: Callable, schema: Optional[dict] = None) -> None:
        """注册工具

        Args:
            name: 工具名称
            func: 工具函数
            schema: 工具 schema
        """
        self._tools[name] = func
        if schema:
            self._tool_schemas.append(schema)

    def unregister_tool(self, name: str) -> None:
        """注销工具"""
        self._tools.pop(name, None)
        self._tool_schemas = [s for s in self._tool_schemas if s.get("name") != name]

    async def call_tool(self, name: str, **kwargs) -> Any:
        """调用工具

        Args:
            name: 工具名称
            **kwargs: 工具参数

        Returns:
            工具执行结果
        """
        if name not in self._tools:
            raise ValueError(f"Tool not found: {name}")

        func = self._tools[name]
        import asyncio

        if asyncio.iscoroutinefunction(func):
            return await func(**kwargs)
        return func(**kwargs)

    def has_tool(self, name: str) -> bool:
        """检查工具是否存在"""
        return name in self._tools

    def list_tools(self) -> list[str]:
        """列出所有工具"""
        return list(self._tools.keys())

    def get_tool_schemas(self) -> list[dict]:
        """获取工具 schemas"""
        return self._tool_schemas.copy()


class AgentMemoryMixin:
    """Agent 记忆管理混合类

    提供与 BaseAgent 兼容的记忆管理功能:
    - 记忆存储/读取
    - 记忆遗忘
    - 记忆清空
    """

    def __init__(self):
        self._memory: dict[str, Any] = {}

    def remember(self, key: str, value: Any) -> None:
        """存储记忆

        Args:
            key: 记忆键
            value: 记忆值
        """
        self._memory[key] = value

    def recall(self, key: str, default: Any = None) -> Any:
        """回忆记忆

        Args:
            key: 记忆键
            default: 默认值

        Returns:
            记忆值
        """
        return self._memory.get(key, default)

    def forget(self, key: str) -> None:
        """遗忘记忆"""
        self._memory.pop(key, None)

    def clear_memory(self) -> None:
        """清空记忆"""
        self._memory.clear()

    def has_memory(self, key: str) -> bool:
        """检查记忆是否存在"""
        return key in self._memory

    def get_memory_keys(self) -> list[str]:
        """获取所有记忆键"""
        return list(self._memory.keys())

    def get_memory(self) -> dict:
        """获取所有记忆"""
        return self._memory.copy()


class AgentHooksMixin:
    """Agent Hooks 管理混合类

    提供 Hooks 注册和触发功能:
    - Hook 注册
    - Hook 触发
    - Hook 列表
    """

    def __init__(self):
        self._hooks: dict[str, list[Callable]] = {}

    def register_hook(self, event: str, handler: Callable) -> None:
        """注册 Hook

        Args:
            event: 事件名称
            handler: 处理函数
        """
        if event not in self._hooks:
            self._hooks[event] = []
        self._hooks[event].append(handler)

    def unregister_hook(self, event: str, handler: Callable) -> None:
        """注销 Hook"""
        if event in self._hooks:
            self._hooks[event] = [h for h in self._hooks[event] if h != handler]

    async def trigger_hooks(self, event: str, context: dict = None) -> list:
        """触发 Hooks

        Args:
            event: 事件名称
            context: 上下文

        Returns:
            Hook 执行结果列表
        """
        results = []
        context = context or {}

        for handler in self._hooks.get(event, []):
            try:
                import asyncio

                if asyncio.iscoroutinefunction(handler):
                    result = await handler(context)
                else:
                    result = handler(context)
                results.append(result)
            except Exception as e:
                results.append({"error": str(e)})

        return results

    def list_hooks(self) -> dict[str, int]:
        """列出所有 Hooks"""
        return {event: len(handlers) for event, handlers in self._hooks.items()}


class AgentExceptionMixin:
    """Agent 异常处理混合类

    提供统一异常处理功能:
    - 异常转换
    - 上下文增强
    - 错误日志
    """

    def __init__(self):
        self._exception_handler = None

    def set_exception_handler(self, handler: Any) -> None:
        """设置异常处理器"""
        self._exception_handler = handler

    def get_exception_handler(self) -> Any:
        """获取异常处理器"""
        return self._exception_handler

    async def safe_execute(self, func: Callable, *args, default: Any = None, **kwargs) -> Any:
        """安全执行函数

        Args:
            func: 要执行的函数
            *args: 位置参数
            default: 异常默认返回值
            **kwargs: 关键字参数

        Returns:
            函数结果或默认值
        """
        if self._exception_handler:
            return await self._exception_handler.safe_execute_async(
                func, *args, default=default, **kwargs
            )

        # 默认实现
        try:
            return (
                await func(*args, **kwargs)
                if asyncio.iscoroutinefunction(func)
                else func(*args, **kwargs)
            )
        except Exception:
            return default

    def _convert_exception(self, exception: Exception) -> Exception:
        """转换异常

        Args:
            exception: 原始异常

        Returns:
            统一异常
        """
        if self._exception_handler:
            return self._exception_handler.handle_exception(exception, reraise=False)

        # 默认返回原始异常
        return exception


import asyncio

__all__ = [
    "AgentToolsMixin",
    "AgentMemoryMixin",
    "AgentHooksMixin",
    "AgentExceptionMixin",
]

"""
MCP Tools - MCP 工具注册协议

提供 MCP 工具的注册、发现和调用功能
"""

import inspect
import logging
from dataclasses import dataclass
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


@dataclass
class MCPTool:
    """MCP 工具定义"""

    name: str
    description: str
    input_schema: dict[str, Any]
    handler: Callable[..., Any]
    is_async: bool = False

    def __post_init__(self):
        self.is_async = inspect.iscoroutinefunction(self.handler)

    async def execute(self, params: dict[str, Any]) -> Any:
        """执行工具"""
        if self.is_async:
            return await self.handler(**params)
        return self.handler(**params)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典 (MCP 协议格式)"""
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.input_schema,
        }


class MCPToolRegistry:
    """MCP 工具注册表"""

    def __init__(self, name: str = "default"):
        self.name = name
        self._tools: dict[str, MCPTool] = {}
        self._categories: dict[str, set[str]] = {}

    def register(
        self,
        name: str,
        description: str,
        input_schema: dict[str, Any],
        category: Optional[str] = None,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """装饰器：注册工具"""

        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            tool = MCPTool(
                name=name,
                description=description,
                input_schema=input_schema,
                handler=func,
            )
            self._tools[name] = tool

            if category:
                if category not in self._categories:
                    self._categories[category] = set()
                self._categories[category].add(name)

            logger.debug(f"Registered MCP tool: {name}")
            return func

        return decorator

    def register_tool(self, tool: MCPTool):
        """直接注册工具"""
        self._tools[tool.name] = tool
        logger.debug(f"Registered MCP tool: {tool.name}")

    def get(self, name: str) -> Optional[MCPTool]:
        """获取工具"""
        return self._tools.get(name)

    def list_tools(self) -> list[dict[str, Any]]:
        """列出所有工具"""
        return [tool.to_dict() for tool in self._tools.values()]

    def list_by_category(self, category: str) -> list[MCPTool]:
        """按分类列出工具"""
        tool_names = self._categories.get(category, set())
        return [self._tools[name] for name in tool_names if name in self._tools]

    def has_tool(self, name: str) -> bool:
        """检查工具是否存在"""
        return name in self._tools

    async def execute_tool(self, name: str, params: dict[str, Any]) -> Any:
        """执行工具"""
        tool = self.get(name)
        if tool is None:
            raise ValueError(f"Tool not found: {name}")
        return await tool.execute(params)

    def get_categories(self) -> list[str]:
        """获取所有分类"""
        return list(self._categories.keys())


# 全局注册表
_global_registry: Optional[MCPToolRegistry] = None


def get_registry(name: str = "default") -> MCPToolRegistry:
    """获取工具注册表"""
    global _global_registry
    if _global_registry is None:
        _global_registry = MCPToolRegistry(name)
    return _global_registry


def mcp_tool(
    name: str,
    description: str,
    input_schema: dict[str, Any],
    category: Optional[str] = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """MCP 工具装饰器 (便捷函数)

    Args:
        name: 工具名称
        description: 工具描述
        input_schema: 输入 schema
        category: 分类 (可选)

    Returns:
        装饰器函数
    """
    registry = get_registry()
    return registry.register(name, description, input_schema, category)


# 预定义的输入 Schema 工厂函数
class Schema:
    """输入 Schema 工厂"""

    @staticmethod
    def object(properties: dict[str, Any], required: list[str]) -> dict[str, Any]:
        """对象类型 Schema"""
        return {
            "type": "object",
            "properties": properties,
            "required": required,
        }

    @staticmethod
    def string(description: str, min_length: Optional[int] = None) -> dict[str, Any]:
        """字符串类型 Schema"""
        result = {"type": "string", "description": description}
        if min_length is not None:
            result["minLength"] = min_length
        return result

    @staticmethod
    def integer(description: str, minimum: Optional[int] = None) -> dict[str, Any]:
        """整数类型 Schema"""
        result = {"type": "integer", "description": description}
        if minimum is not None:
            result["minimum"] = minimum
        return result

    @staticmethod
    def number(description: str, minimum: Optional[float] = None) -> dict[str, Any]:
        """数字类型 Schema"""
        result = {"type": "number", "description": description}
        if minimum is not None:
            result["minimum"] = minimum
        return result

    @staticmethod
    def boolean(description: str) -> dict[str, Any]:
        """布尔类型 Schema"""
        return {"type": "boolean", "description": description}

    @staticmethod
    def array(
        items: dict[str, Any], description: str, min_items: Optional[int] = None
    ) -> dict[str, Any]:
        """数组类型 Schema"""
        result = {"type": "array", "items": items, "description": description}
        if min_items is not None:
            result["minItems"] = min_items
        return result

    @staticmethod
    def enum(values: list[Any], description: str) -> dict[str, Any]:
        """枚举类型 Schema"""
        return {"type": "string", "enum": values, "description": description}

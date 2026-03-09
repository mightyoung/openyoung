"""
MCP Tool Types - MCP 工具类型定义

提供 MCP 工具的类型化支持，增强开发体验和类型安全
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional


class MCPToolCategory(Enum):
    """MCP 工具分类"""

    FILESYSTEM = "filesystem"
    DATABASE = "database"
    NETWORK = "network"
    BROWSER = "browser"
    MESSAGING = "messaging"
    SEARCH = "search"
    MEMORY = "memory"
    CUSTOM = "custom"


@dataclass
class MCPToolSchema:
    """MCP 工具 Schema 定义"""

    name: str
    description: str
    category: MCPToolCategory
    input_schema: dict[str, Any]
    output_schema: Optional[dict[str, Any]] = None
    examples: Optional[list[dict[str, Any]]] = None


# 预定义 MCP 工具 Schema
MCP_TOOL_SCHEMAS: dict[str, MCPToolSchema] = {
    # Filesystem
    "filesystem_read_file": MCPToolSchema(
        name="filesystem_read_file",
        description="Read contents of a file",
        category=MCPToolCategory.FILESYSTEM,
        input_schema={
            "type": "object",
            "properties": {"path": {"type": "string", "description": "Path to the file"}},
            "required": ["path"],
        },
        output_schema={"type": "string"},
    ),
    "filesystem_write_file": MCPToolSchema(
        name="filesystem_write_file",
        description="Write content to a file",
        category=MCPToolCategory.FILESYSTEM,
        input_schema={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to the file"},
                "content": {"type": "string", "description": "Content to write"},
            },
            "required": ["path", "content"],
        },
    ),
    "filesystem_list_directory": MCPToolSchema(
        name="filesystem_list_directory",
        description="List files in a directory",
        category=MCPToolCategory.FILESYSTEM,
        input_schema={
            "type": "object",
            "properties": {"path": {"type": "string", "description": "Directory path"}},
            "required": ["path"],
        },
    ),
    # Database
    "postgres_query": MCPToolSchema(
        name="postgres_query",
        description="Execute a PostgreSQL query",
        category=MCPToolCategory.DATABASE,
        input_schema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "SQL query"},
                "params": {"type": "array", "description": "Query parameters"},
            },
            "required": ["query"],
        },
    ),
    "sqlite_query": MCPToolSchema(
        name="sqlite_query",
        description="Execute a SQLite query",
        category=MCPToolCategory.DATABASE,
        input_schema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "SQL query"},
                "params": {"type": "array", "description": "Query parameters"},
            },
            "required": ["query"],
        },
    ),
    # Network
    "fetch_url": MCPToolSchema(
        name="fetch_url",
        description="Fetch content from a URL",
        category=MCPToolCategory.NETWORK,
        input_schema={
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "URL to fetch"},
                "method": {"type": "string", "description": "HTTP method"},
                "headers": {"type": "object", "description": "HTTP headers"},
            },
            "required": ["url"],
        },
    ),
    # Browser
    "puppeteer_navigate": MCPToolSchema(
        name="puppeteer_navigate",
        description="Navigate browser to URL",
        category=MCPToolCategory.BROWSER,
        input_schema={
            "type": "object",
            "properties": {"url": {"type": "string", "description": "URL to navigate to"}},
            "required": ["url"],
        },
    ),
    "puppeteer_click": MCPToolSchema(
        name="puppeteer_click",
        description="Click an element",
        category=MCPToolCategory.BROWSER,
        input_schema={
            "type": "object",
            "properties": {"selector": {"type": "string", "description": "CSS selector"}},
            "required": ["selector"],
        },
    ),
    # Messaging
    "slack_send_message": MCPToolSchema(
        name="slack_send_message",
        description="Send a message to Slack",
        category=MCPToolCategory.MESSAGING,
        input_schema={
            "type": "object",
            "properties": {
                "channel": {"type": "string", "description": "Slack channel"},
                "text": {"type": "string", "description": "Message text"},
            },
            "required": ["channel", "text"],
        },
    ),
    # GitHub
    "github_get_issue": MCPToolSchema(
        name="github_get_issue",
        description="Get a GitHub issue",
        category=MCPToolCategory.CUSTOM,
        input_schema={
            "type": "object",
            "properties": {
                "owner": {"type": "string", "description": "Repository owner"},
                "repo": {"type": "string", "description": "Repository name"},
                "issue_number": {"type": "integer", "description": "Issue number"},
            },
            "required": ["owner", "repo", "issue_number"],
        },
    ),
    "github_create_issue": MCPToolSchema(
        name="github_create_issue",
        description="Create a GitHub issue",
        category=MCPToolCategory.CUSTOM,
        input_schema={
            "type": "object",
            "properties": {
                "owner": {"type": "string", "description": "Repository owner"},
                "repo": {"type": "string", "description": "Repository name"},
                "title": {"type": "string", "description": "Issue title"},
                "body": {"type": "string", "description": "Issue body"},
            },
            "required": ["owner", "repo", "title"],
        },
    ),
    # Memory
    "memory_search": MCPToolSchema(
        name="memory_search",
        description="Search memory/knowledge base",
        category=MCPToolCategory.MEMORY,
        input_schema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "limit": {"type": "integer", "description": "Max results"},
            },
            "required": ["query"],
        },
    ),
    "memory_store": MCPToolSchema(
        name="memory_store",
        description="Store to memory/knowledge base",
        category=MCPToolCategory.MEMORY,
        input_schema={
            "type": "object",
            "properties": {
                "key": {"type": "string", "description": "Memory key"},
                "value": {"type": "string", "description": "Memory value"},
                "namespace": {"type": "string", "description": "Namespace"},
            },
            "required": ["key", "value"],
        },
    ),
}


def get_tool_schema(tool_name: str) -> Optional[MCPToolSchema]:
    """获取工具 Schema"""
    return MCP_TOOL_SCHEMAS.get(tool_name)


def get_tools_by_category(category: MCPToolCategory) -> list[MCPToolSchema]:
    """获取指定分类的所有工具"""
    return [s for s in MCP_TOOL_SCHEMAS.values() if s.category == category]


def validate_tool_input(tool_name: str, params: dict) -> tuple[bool, str]:
    """验证工具输入参数

    Args:
        tool_name: 工具名称
        params: 输入参数

    Returns:
        (is_valid, error_message)
    """
    schema = get_tool_schema(tool_name)
    if not schema:
        return True, ""  # 未知工具跳过验证

    input_schema = schema.input_schema
    required = input_schema.get("required", [])

    # 检查必需参数
    for field in required:
        if field not in params:
            return False, f"Missing required parameter: {field}"

    # 检查类型
    properties = input_schema.get("properties", {})
    for key, value in params.items():
        if key in properties:
            expected_type = properties[key].get("type")
            if expected_type == "integer" and not isinstance(value, int):
                return False, f"Parameter {key} must be integer"
            elif expected_type == "array" and not isinstance(value, list):
                return False, f"Parameter {key} must be array"
            elif expected_type == "object" and not isinstance(value, dict):
                return False, f"Parameter {key} must be object"

    return True, ""

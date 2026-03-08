"""
Tool Contract - 2026 AI Agent Best Practice

基于 2026 年行业标准，实现 Tool Contract 验证层：
- 类型化输入/输出验证
- 运行时类型检查
- 错误追踪

参考:
- LangGraph Tool Schema
- OpenAI Agent SDK Tool Definitions
- RagaAI Catalyst Tool Contracts
"""

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ToolType(Enum):
    """工具类型"""
    BASH = "bash"
    READ = "read"
    WRITE = "write"
    EDIT = "edit"
    GLOB = "glob"
    GREP = "grep"
    WEB_FETCH = "web_fetch"
    GIT = "git"
    MCP = "mcp"


@dataclass
class FieldSchema:
    """字段模式定义"""
    name: str
    type: str  # "string", "integer", "boolean", "array", "object"
    description: str = ""
    required: bool = True
    default: Any = None
    pattern: str = ""  # 正则验证
    enum: list[Any] = field(default_factory=list)  # 枚举值
    min_value: int | float | None = None
    max_value: int | float | None = None


@dataclass
class ToolContract:
    """工具合约定义"""
    name: str
    description: str
    input_schema: list[FieldSchema] = field(default_factory=list)
    output_type: str = "string"  # "string", "object", "boolean", "integer"
    required_permissions: list[str] = field(default_factory=list)
    allowed_paths: list[str] = field(default_factory=list)  # 允许的文件路径模式
    forbidden_patterns: list[str] = field(default_factory=list)  # 禁止的模式

    def validate_input(self, arguments: dict[str, Any]) -> tuple[bool, str | None]:
        """
        验证输入参数

        Returns:
            (is_valid, error_message)
        """
        for field_schema in self.input_schema:
            value = arguments.get(field_schema.name)

            # 检查必填字段
            if field_schema.required and value is None:
                return False, f"Missing required field: {field_schema.name}"

            if value is None:
                continue

            # 类型检查
            expected_type = field_schema.type
            if expected_type == "string" and not isinstance(value, str):
                return False, f"Field '{field_schema.name}' must be string, got {type(value).__name__}"
            elif expected_type == "integer" and not isinstance(value, int):
                return False, f"Field '{field_schema.name}' must be integer, got {type(value).__name__}"
            elif expected_type == "boolean" and not isinstance(value, bool):
                return False, f"Field '{field_schema.name}' must be boolean, got {type(value).__name__}"
            elif expected_type == "array" and not isinstance(value, list):
                return False, f"Field '{field_schema.name}' must be array, got {type(value).__name__}"

            # 枚举检查
            if field_schema.enum and value not in field_schema.enum:
                return False, f"Field '{field_schema.name}' must be one of {field_schema.enum}"

            # 正则验证
            if field_schema.pattern and isinstance(value, str):
                if not re.match(field_schema.pattern, value):
                    return False, f"Field '{field_schema.name}' does not match pattern: {field_schema.pattern}"

            # 范围检查
            if field_schema.min_value is not None:
                if isinstance(value, (int, float)) and value < field_schema.min_value:
                    return False, f"Field '{field_schema.name}' must be >= {field_schema.min_value}"
            if field_schema.max_value is not None:
                if isinstance(value, (int, float)) and value > field_schema.max_value:
                    return False, f"Field '{field_schema.name}' must be <= {field_schema.max_value}"

        return True, None


class ToolContractRegistry:
    """工具合约注册表"""

    def __init__(self):
        self._contracts: dict[str, ToolContract] = {}
        self._setup_default_contracts()

    def _setup_default_contracts(self):
        """设置默认工具合约"""

        # Bash 工具合约
        self.register(ToolContract(
            name="bash",
            description="Execute shell command",
            input_schema=[
                FieldSchema("command", "string", "Shell command to execute", required=True),
                FieldSchema("description", "string", "Command description", required=False),
            ],
            required_permissions=["bash"],
        ))

        # Write 工具合约
        self.register(ToolContract(
            name="write",
            description="Write content to file",
            input_schema=[
                FieldSchema("filePath", "string", "File path to write", required=True),
                FieldSchema("content", "string", "Content to write", required=True),
            ],
            allowed_paths=["**/src/**", "**/tests/**", "**/output/**", "**/docs/**", "**/config/**"],
        ))

        # Edit 工具合约
        self.register(ToolContract(
            name="edit",
            description="Edit file content",
            input_schema=[
                FieldSchema("filePath", "string", "File path to edit", required=True),
                FieldSchema("old_content", "string", "Content to replace", required=True),
                FieldSchema("new_content", "string", "New content", required=True),
            ],
            allowed_paths=["**/src/**", "**/tests/**", "**/docs/**"],
        ))

        # Read 工具合约
        self.register(ToolContract(
            name="read",
            description="Read file content",
            input_schema=[
                FieldSchema("filePath", "string", "File path to read", required=True),
                FieldSchema("limit", "integer", "Max lines to read", required=False, min_value=1, max_value=10000),
                FieldSchema("offset", "integer", "Line offset to start", required=False, min_value=1),
            ],
            allowed_paths=["**"],  # 允许读取所有文件
        ))

        # Glob 工具合约
        self.register(ToolContract(
            name="glob",
            description="Find files by pattern",
            input_schema=[
                FieldSchema("pattern", "string", "Glob pattern", required=True),
            ],
        ))

        # Grep 工具合约
        self.register(ToolContract(
            name="grep",
            description="Search in files",
            input_schema=[
                FieldSchema("pattern", "string", "Regex pattern", required=True),
                FieldSchema("path", "string", "Search path", required=False, default="."),
                FieldSchema("include", "string", "File include filter", required=False),
            ],
        ))

        # Web Fetch 工具合约
        self.register(ToolContract(
            name="web_fetch",
            description="Fetch web content",
            input_schema=[
                FieldSchema("url", "string", "URL to fetch", required=True,
                           pattern=r"^https?://"),
                FieldSchema("selector", "string", "CSS selector for content extraction", required=False),
            ],
        ))

        # Git 工具合约
        self.register(ToolContract(
            name="git",
            description="Execute git command",
            input_schema=[
                FieldSchema("command", "string", "Git command (status, log, diff, etc.)",
                           required=True, enum=["status", "log", "diff", "branch", "pull", "fetch"]),
                FieldSchema("repo_path", "string", "Repository path", required=False, default="."),
            ],
        ))

    def register(self, contract: ToolContract):
        """注册工具合约"""
        self._contracts[contract.name] = contract

    def get(self, tool_name: str) -> ToolContract | None:
        """获取工具合约"""
        return self._contracts.get(tool_name)

    def validate(self, tool_name: str, arguments: dict[str, Any]) -> tuple[bool, str | None]:
        """
        验证工具调用

        Returns:
            (is_valid, error_message)
        """
        contract = self._contracts.get(tool_name)
        if not contract:
            return True, None  # 无合约，允许执行

        return contract.validate_input(arguments)

    def get_allowed_paths(self, tool_name: str) -> list[str]:
        """获取工具允许的路径"""
        contract = self._contracts.get(tool_name)
        return contract.allowed_paths if contract else []


# 全局注册表实例
_global_registry: ToolContractRegistry | None = None


def get_tool_contract_registry() -> ToolContractRegistry:
    """获取全局工具合约注册表"""
    global _global_registry
    if _global_registry is None:
        _global_registry = ToolContractRegistry()
    return _global_registry

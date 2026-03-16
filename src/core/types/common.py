"""
Core Types - Common Module

Common type definitions (Message, Tool, etc.)
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class MessageRole(Enum):
    """消息角色"""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


@dataclass
class Message:
    """消息"""

    role: MessageRole
    content: str
    name: str | None = None
    tool_call_id: str | None = None


@dataclass
class Tool:
    """工具定义"""

    name: str
    description: str
    input_schema: dict[str, Any] = field(default_factory=dict)

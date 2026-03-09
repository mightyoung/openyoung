"""
BaseChannel - 消息通道基类

定义所有消息通道的通用接口
"""

from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

# R2-2: 使用 core/types 中的 MessageRole，避免重复定义
# 保留此处的别名以保持向后兼容
try:
    from src.core.types import MessageRole as CoreMessageRole

    MessageRole = CoreMessageRole
except ImportError:
    # 如果导入失败，使用本地定义（向后兼容）
    class MessageRole(str, Enum):
        """消息角色"""

        USER = "user"
        ASSISTANT = "assistant"
        SYSTEM = "system"
        TOOL = "tool"


@dataclass
class ChannelMessage:
    """统一的消息格式"""

    id: str
    role: MessageRole
    content: str
    platform: str
    channel_id: str
    user_id: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)
    reply_to: str | None = None  # 回复的消息ID


@dataclass
class ChannelUser:
    """统一的用户格式"""

    id: str
    name: str
    platform: str
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseChannel(ABC):
    """消息通道抽象基类

    所有平台适配器需继承此类并实现抽象方法
    """

    def __init__(self, config: dict[str, Any] = None):
        self.config = config or {}
        self._message_handler: Callable | None = None
        self._connected = False

    @property
    @abstractmethod
    def platform(self) -> str:
        """返回平台名称"""
        pass

    @abstractmethod
    async def connect(self) -> bool:
        """连接到平台"""
        pass

    @abstractmethod
    async def disconnect(self) -> bool:
        """断开连接"""
        pass

    @abstractmethod
    async def send_message(self, message: ChannelMessage, reply_to: str | None = None) -> bool:
        """发送消息"""
        pass

    @abstractmethod
    async def send_markdown(self, message: ChannelMessage, reply_to: str | None = None) -> bool:
        """发送 Markdown 消息"""
        pass

    @abstractmethod
    async def send_image(self, message: ChannelMessage, image_url: str) -> bool:
        """发送图片消息"""
        pass

    def on_message(self, handler: Callable[[ChannelMessage], Any]):
        """设置消息处理器

        Args:
            handler: 异步函数，接受 ChannelMessage，返回处理结果
        """
        self._message_handler = handler

    async def _notify_handler(self, message: ChannelMessage):
        """触发消息处理器"""
        if self._message_handler:
            try:
                await self._message_handler(message)
            except Exception as e:
                print(f"[{self.platform}] Message handler error: {e}")

    def is_connected(self) -> bool:
        """检查是否已连接"""
        return self._connected

    async def health_check(self) -> bool:
        """健康检查"""
        return self._connected


class ChannelConfig:
    """通道配置"""

    def __init__(self, platform: str, enabled: bool = True, **kwargs):
        self.platform = platform
        self.enabled = enabled
        self.config = kwargs

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ChannelConfig":
        """从字典创建配置"""
        return cls(
            platform=data.get("platform", ""),
            enabled=data.get("enabled", True),
            **{k: v for k, v in data.items() if k not in ["platform", "enabled"]},
        )

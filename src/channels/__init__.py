"""
Channels Package - 消息通道模块

支持多平台消息接入:
- CLI (命令行)
- Telegram
- Discord
- QQ (Go-CQHTTP)
- 钉钉
- 飞书
"""

from .base import (
    BaseChannel,
    ChannelConfig,
    ChannelMessage,
    ChannelUser,
    MessageRole,
)
from .cli import CLIChannel, REPLChannel
from .dingtalk import DingTalkCallbackChannel, DingTalkChannel
from .discord import DiscordChannel
from .feishu import FeishuChannel, FeishuWebhookChannel
from .manager import ChannelManager, MessageContext
from .qq import QQChannel
from .telegram import TelegramChannel

__all__ = [
    # Base
    "BaseChannel",
    "ChannelMessage",
    "ChannelUser",
    "ChannelConfig",
    "MessageRole",
    # Manager
    "ChannelManager",
    "MessageContext",
    # Channels
    "CLIChannel",
    "REPLChannel",
    "TelegramChannel",
    "DiscordChannel",
    "QQChannel",
    "DingTalkChannel",
    "DingTalkCallbackChannel",
    "FeishuChannel",
    "FeishuWebhookChannel",
]

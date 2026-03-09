"""
ChannelManager - 通道管理器

负责管理所有消息通道的注册、消息路由和事件分发
"""

import asyncio
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field

from .base import BaseChannel, ChannelMessage


@dataclass
class MessageContext:
    """消息上下文"""

    message: ChannelMessage
    platform: str
    channel_id: str
    user_id: str
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))


class ChannelManager:
    """通道管理器

    职责:
    - 注册和管理所有通道
    - 消息路由和分发
    - 统一的事件处理
    """

    def __init__(self, agent=None):
        self._channels: dict[str, BaseChannel] = {}
        self._agent = agent
        self._message_handlers: list[Callable] = []
        self._command_handlers: dict[str, Callable] = {}

    def register_channel(self, channel: BaseChannel) -> bool:
        """注册通道

        Args:
            channel: 通道实例

        Returns:
            是否注册成功
        """
        platform = channel.platform

        if platform in self._channels:
            print(f"[ChannelManager] Channel {platform} already registered, replacing")
            # 断开旧连接
            asyncio.create_task(self._channels[platform].disconnect())

        # 设置消息处理器
        channel.on_message(self._handle_message)
        self._channels[platform] = channel

        print(f"[ChannelManager] Registered channel: {platform}")
        return True

    def unregister_channel(self, platform: str) -> bool:
        """注销通道"""
        if platform not in self._channels:
            return False

        channel = self._channels[platform]
        asyncio.create_task(channel.disconnect())
        del self._channels[platform]

        print(f"[ChannelManager] Unregistered channel: {platform}")
        return True

    def get_channel(self, platform: str) -> BaseChannel | None:
        """获取通道"""
        return self._channels.get(platform)

    def list_channels(self) -> list[str]:
        """列出所有已注册的通道"""
        return list(self._channels.keys())

    async def connect_all(self) -> dict[str, bool]:
        """连接所有通道"""
        results = {}
        for platform, channel in self._channels.items():
            try:
                success = await channel.connect()
                results[platform] = success
            except Exception as e:
                print(f"[ChannelManager] Failed to connect {platform}: {e}")
                results[platform] = False
        return results

    async def disconnect_all(self) -> None:
        """断开所有通道"""
        for platform, channel in self._channels.items():
            try:
                await channel.disconnect()
            except Exception as e:
                print(f"[ChannelManager] Failed to disconnect {platform}: {e}")

    def add_message_handler(self, handler: Callable) -> None:
        """添加消息处理器"""
        self._message_handlers.append(handler)

    def register_command(self, command: str, handler: Callable) -> None:
        """注册命令处理器"""
        self._command_handlers[command] = handler

    async def _handle_message(self, message: ChannelMessage) -> None:
        """处理接收到的消息"""
        # 检查是否是命令
        if message.content.startswith("/"):
            await self._handle_command(message)
            return

        # 创建消息上下文
        context = MessageContext(
            message=message,
            platform=message.platform,
            channel_id=message.channel_id,
            user_id=message.user_id,
        )

        # 触发消息处理器
        for handler in self._message_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(context)
                else:
                    handler(context)
            except Exception as e:
                print(f"[ChannelManager] Handler error: {e}")

        # 如果有 Agent，调用 Agent 处理
        if self._agent:
            try:
                result = await self._agent.run(message.content)
                await self._send_response(message, result)
            except Exception as e:
                print(f"[ChannelManager] Agent error: {e}")
                await self._send_error(message, str(e))

    async def _handle_command(self, message: ChannelMessage) -> None:
        """处理命令"""
        # 解析命令 (去除 / 前缀)
        content = message.content[1:].strip()
        parts = content.split()
        command = parts[0].lower() if parts else ""
        args = parts[1:] if len(parts) > 1 else []

        # 查找命令处理器
        handler = self._command_handlers.get(command)
        if handler:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(message, args)
                else:
                    handler(message, args)
            except Exception as e:
                print(f"[ChannelManager] Command error: {e}")
                await self._send_error(message, f"Command error: {e}")
        else:
            await self._send_error(message, f"Unknown command: /{command}")

    async def _send_response(self, message: ChannelMessage, response: str) -> None:
        """发送响应"""
        channel = self._channels.get(message.platform)
        if channel:
            response_msg = ChannelMessage(
                id=str(uuid.uuid4()),
                role="assistant",
                content=response,
                platform=message.platform,
                channel_id=message.channel_id,
                user_id=message.user_id,
                reply_to=message.id,
            )
            await channel.send_message(response_msg, reply_to=message.id)

    async def _send_error(self, message: ChannelMessage, error: str) -> None:
        """发送错误消息"""
        channel = self._channels.get(message.platform)
        if channel:
            error_msg = ChannelMessage(
                id=str(uuid.uuid4()),
                role="assistant",
                content=f"Error: {error}",
                platform=message.platform,
                channel_id=message.channel_id,
                user_id=message.user_id,
            )
            await channel.send_message(error_msg)

    def set_agent(self, agent) -> None:
        """设置 Agent 实例"""
        self._agent = agent


# 内置命令处理器
async def help_command(message: ChannelMessage, args: list[str]) -> None:
    """帮助命令"""
    help_text = """Available commands:
/help - Show this help
/new - Start new session
/stop - Stop current task
/list - List available channels"""
    # 这里需要访问 channel，可以通过 message 获取
    print(f"[Command] /help from {message.user_id}")


async def new_session_command(message: ChannelMessage, args: list[str]) -> None:
    """新建会话命令"""
    print(f"[Command] /new from {message.user_id}")


async def stop_task_command(message: ChannelMessage, args: list[str]) -> None:
    """停止任务命令"""
    print(f"[Command] /stop from {message.user_id}")

"""
CLI Channel - 命令行通道适配器

保留现有的 CLI 交互方式
"""

import asyncio
import uuid
from typing import Any

from .base import BaseChannel, ChannelMessage, MessageRole


class CLIChannel(BaseChannel):
    """CLI 通道适配器

    提供命令行交互支持，兼容现有 REPL
    """

    def __init__(self, config: dict[str, Any] = None):
        super().__init__(config)
        self._input_queue: asyncio.Queue = asyncio.Queue()
        self._running = False

    @property
    def platform(self) -> str:
        return "cli"

    async def connect(self) -> bool:
        """连接 CLI (实际上是启动输入监听)"""
        self._connected = True
        self._running = True
        print("[CLI] Channel connected")
        return True

    async def disconnect(self) -> bool:
        """断开 CLI"""
        self._connected = False
        self._running = False
        print("[CLI] Channel disconnected")
        return True

    async def send_message(
        self,
        message: ChannelMessage,
        reply_to: str | None = None
    ) -> bool:
        """发送消息到 CLI"""
        if not self._connected:
            return False

        # 输出消息
        print(f"\n[Assistant]: {message.content}\n")
        return True

    async def send_markdown(
        self,
        message: ChannelMessage,
        reply_to: str | None = None
    ) -> bool:
        """发送 Markdown 消息"""
        # CLI 不支持 Markdown，直接发送纯文本
        return await self.send_message(message, reply_to)

    async def send_image(
        self,
        message: ChannelMessage,
        image_url: str
    ) -> bool:
        """发送图片消息"""
        # CLI 不支持图片
        print(f"[CLI] Image not supported: {image_url}")
        return False

    async def read_input(self) -> ChannelMessage | None:
        """读取用户输入"""
        try:
            content = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: input("\n[You]: ")
                ),
                timeout=self.config.get("timeout", 300)
            )

            if content.strip():
                return ChannelMessage(
                    id=str(uuid.uuid4()),
                    role=MessageRole.USER,
                    content=content,
                    platform=self.platform,
                    channel_id="cli",
                    user_id="local",
                )
        except asyncio.TimeoutError:
            pass
        except EOFError:
            self._running = False
        return None

    async def start_interactive(self) -> None:
        """启动交互式 CLI"""
        await self.connect()

        print("=" * 50)
        print("OpenYoung CLI - Interactive Mode")
        print("Type 'exit' or 'quit' to stop")
        print("=" * 50)

        while self._running:
            message = await self.read_input()
            if message:
                if message.content.lower() in ["exit", "quit"]:
                    break
                await self._notify_handler(message)

        await self.disconnect()


class REPLChannel(CLIChannel):
    """REPL 通道 - 保留现有 REPL 兼容性"""

    def __init__(self, config: dict[str, Any] = None):
        super().__init__(config)
        self._history: list = []

    async def send_message(
        self,
        message: ChannelMessage,
        reply_to: str | None = None
    ) -> bool:
        """发送消息并记录历史"""
        result = await super().send_message(message, reply_to)
        if result:
            self._history.append(message)
        return result

    def get_history(self) -> list:
        """获取历史消息"""
        return self._history.copy()

    def clear_history(self) -> None:
        """清空历史"""
        self._history.clear()

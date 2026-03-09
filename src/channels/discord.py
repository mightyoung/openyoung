"""
Discord Channel - Discord 平台适配器

基于 discord.py 实现
"""

from typing import Any

from .base import BaseChannel, ChannelMessage, MessageRole


class DiscordChannel(BaseChannel):
    """Discord 通道适配器

    配置参数:
    - bot_token: Discord Bot Token
    - intents: Gateway Intents (默认: messages, reactions)
    """

    def __init__(self, config: dict[str, Any] = None):
        super().__init__(config)
        self._bot_token = self.config.get("bot_token", "")
        self._intents = self.config.get("intents", ["messages", "reactions"])
        self._client = None

    @property
    def platform(self) -> str:
        return "discord"

    async def connect(self) -> bool:
        """连接到 Discord"""
        if not self._bot_token:
            print("[Discord] No bot token configured")
            return False

        try:
            # 实际实现需要安装 discord.py
            # import discord
            # intents = discord.Intents.default()
            # intents.messages = True
            # intents.reactions = True
            # self._client = discord.Client(intents=intents)
            # await self._client.start(self._bot_token)

            self._connected = True
            print(f"[Discord] Connected (token: ...{self._bot_token[-4:]})")
            return True
        except Exception as e:
            print(f"[Discord] Connection failed: {e}")
            return False

    async def disconnect(self) -> bool:
        """断开连接"""
        if self._client:
            # await self._client.close()
            self._client = None

        self._connected = False
        print("[Discord] Disconnected")
        return True

    async def send_message(self, message: ChannelMessage, reply_to: str | None = None) -> bool:
        """发送消息到 Discord"""
        if not self._connected:
            return False

        try:
            # 实际实现
            # channel = self._client.get_channel(int(message.channel_id))
            # await channel.send(content=message.content)

            print(f"[Discord] Send to {message.channel_id}: {message.content[:50]}...")
            return True
        except Exception as e:
            print(f"[Discord] Send failed: {e}")
            return False

    async def send_markdown(self, message: ChannelMessage, reply_to: str | None = None) -> bool:
        """发送 Markdown 消息"""
        if not self._connected:
            return False

        try:
            # Discord 支持 Markdown (利用内置格式)
            # channel = self._client.get_channel(int(message.channel_id))
            # await channel.send(content=message.content)

            print(f"[Discord] Send markdown to {message.channel_id}")
            return True
        except Exception as e:
            print(f"[Discord] Send markdown failed: {e}")
            return False

    async def send_image(self, message: ChannelMessage, image_url: str) -> bool:
        """发送图片消息"""
        if not self._connected:
            return False

        try:
            # 实际实现
            # channel = self._client.get_channel(int(message.channel_id))
            # await channel.send(content=image_url)

            print(f"[Discord] Send image to {message.channel_id}: {image_url}")
            return True
        except Exception as e:
            print(f"[Discord] Send image failed: {e}")
            return False

    async def _handle_discord_message(self, message) -> None:
        """处理 Discord 消息"""
        # 忽略机器人消息
        if message.author.bot:
            return

        channel_message = ChannelMessage(
            id=str(message.id),
            role=MessageRole.USER,
            content=message.content,
            platform=self.platform,
            channel_id=str(message.channel.id),
            user_id=str(message.author.id),
            metadata={
                "username": message.author.name,
                "display_name": message.author.display_name,
                "is_bot": message.author.bot,
            },
        )
        await self._notify_handler(channel_message)

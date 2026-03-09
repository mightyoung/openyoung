"""
Telegram Channel - Telegram 平台适配器

基于 python-telegram-bot 实现
"""

import asyncio
from typing import Any

from .base import BaseChannel, ChannelMessage, MessageRole


class TelegramChannel(BaseChannel):
    """Telegram 通道适配器

    配置参数:
    - bot_token: Telegram Bot Token
    - api_base_url: API 基础 URL (可选)
    """

    def __init__(self, config: dict[str, Any] = None):
        super().__init__(config)
        self._bot_token = self.config.get("bot_token", "")
        self._api_base_url = self.config.get("api_base_url")
        self._update_id = 0
        self._polling_task = None

    @property
    def platform(self) -> str:
        return "telegram"

    async def connect(self) -> bool:
        """连接到 Telegram"""
        if not self._bot_token:
            print("[Telegram] No bot token configured")
            return False

        try:
            # 测试 API 连接
            # 实际实现需要安装 python-telegram-bot
            # from telegram import Bot
            # self._bot = Bot(token=self._bot_token, base_url=self._api_base_url)
            # await self._bot.get_me()

            self._connected = True
            print(f"[Telegram] Connected (token: ...{self._bot_token[-4:]})")
            return True
        except Exception as e:
            print(f"[Telegram] Connection failed: {e}")
            return False

    async def disconnect(self) -> bool:
        """断开连接"""
        if self._polling_task:
            self._polling_task.cancel()
            self._polling_task = None

        self._connected = False
        print("[Telegram] Disconnected")
        return True

    async def send_message(self, message: ChannelMessage, reply_to: str | None = None) -> bool:
        """发送消息到 Telegram"""
        if not self._connected:
            return False

        try:
            # 实际实现
            # await self._bot.send_message(
            #     chat_id=message.channel_id,
            #     text=message.content,
            #     reply_to_message_id=reply_to
            # )

            # 模拟发送
            print(f"[Telegram] Send to {message.channel_id}: {message.content[:50]}...")
            return True
        except Exception as e:
            print(f"[Telegram] Send failed: {e}")
            return False

    async def send_markdown(self, message: ChannelMessage, reply_to: str | None = None) -> bool:
        """发送 Markdown 消息"""
        if not self._connected:
            return False

        try:
            # 实际实现
            # await self._bot.send_message(
            #     chat_id=message.channel_id,
            #     text=message.content,
            #     parse_mode="MarkdownV2",
            #     reply_to_message_id=reply_to
            # )

            print(f"[Telegram] Send markdown to {message.channel_id}")
            return True
        except Exception as e:
            print(f"[Telegram] Send markdown failed: {e}")
            return False

    async def send_image(self, message: ChannelMessage, image_url: str) -> bool:
        """发送图片消息"""
        if not self._connected:
            return False

        try:
            # 实际实现
            # await self._bot.send_photo(
            #     chat_id=message.channel_id,
            #     photo=image_url
            # )

            print(f"[Telegram] Send image to {message.channel_id}: {image_url}")
            return True
        except Exception as e:
            print(f"[Telegram] Send image failed: {e}")
            return False

    async def _start_polling(self) -> None:
        """开始轮询消息"""
        while self._connected:
            try:
                # 实际实现
                # updates = await self._bot.get_updates(offset=self._update_id, timeout=30)
                # for update in updates:
                #     if update.message:
                #         await self._handle_telegram_message(update.message)
                #     self._update_id = update.update_id + 1

                await asyncio.sleep(1)
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"[Telegram] Polling error: {e}")
                await asyncio.sleep(5)

    async def _handle_telegram_message(self, message) -> None:
        """处理 Telegram 消息"""
        channel_message = ChannelMessage(
            id=str(message.message_id),
            role=MessageRole.USER,
            content=message.text or "",
            platform=self.platform,
            channel_id=str(message.chat.id),
            user_id=str(message.from_user.id),
            metadata={
                "username": message.from_user.username,
                "first_name": message.from_user.first_name,
            },
        )
        await self._notify_handler(channel_message)

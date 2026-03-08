"""
QQ Channel - QQ 平台适配器

基于 Go-CQHTTP 实现
"""

import uuid
from typing import Any

from .base import BaseChannel, ChannelMessage, MessageRole


class QQChannel(BaseChannel):
    """QQ 通道适配器

    基于 Go-CQHTTP HTTP API 实现

    配置参数:
    - http_host: CQHTTP 服务地址 (默认: localhost)
    - http_port: CQHTTP 端口 (默认: 5700)
    - access_token: 访问令牌 (可选)
    """

    def __init__(self, config: dict[str, Any] = None):
        super().__init__(config)
        self._http_host = self.config.get("http_host", "localhost")
        self._http_port = self.config.get("http_port", 5700)
        self._access_token = self.config.get("access_token", "")
        self._http_client = None

    @property
    def platform(self) -> str:
        return "qq"

    async def connect(self) -> bool:
        """连接到 CQHTTP"""
        try:
            import aiohttp
            self._http_client = aiohttp.ClientSession()

            # 测试连接
            url = f"http://{self._http_host}:{self._http_port}/get_login_info"
            headers = {}
            if self._access_token:
                headers["Authorization"] = f"Bearer {self._access_token}"

            async with self._http_client.get(url, headers=headers) as resp:
                if resp.status == 200:
                    self._connected = True
                    print(f"[QQ] Connected to CQHTTP at {self._http_host}:{self._http_port}")
                    return True
                else:
                    print(f"[QQ] CQHTTP returned status: {resp.status}")
                    return False
        except Exception as e:
            print(f"[QQ] Connection failed: {e}")
            return False

    async def disconnect(self) -> bool:
        """断开连接"""
        if self._http_client:
            await self._http_client.close()
            self._http_client = None

        self._connected = False
        print("[QQ] Disconnected")
        return True

    async def send_message(
        self,
        message: ChannelMessage,
        reply_to: str | None = None
    ) -> bool:
        """发送消息到 QQ"""
        if not self._connected or not self._http_client:
            return False

        try:

            url = f"http://{self._http_host}:{self._http_port}/send_private_msg"
            data = {
                "user_id": int(message.user_id),
                "message": message.content,
            }
            headers = {}
            if self._access_token:
                headers["Authorization"] = f"Bearer {self._access_token}"

            async with self._http_client.post(url, json=data, headers=headers) as resp:
                result = await resp.json()
                if result.get("status") == "ok":
                    print(f"[QQ] Sent to user {message.user_id}")
                    return True
                else:
                    print(f"[QQ] Send failed: {result}")
                    return False
        except Exception as e:
            print(f"[QQ] Send error: {e}")
            return False

    async def send_markdown(
        self,
        message: ChannelMessage,
        reply_to: str | None = None
    ) -> bool:
        """发送 Markdown 消息 (CQ 码)"""
        if not self._connected:
            return False

        # QQ 使用 CQ 码，不支持直接 Markdown
        # 可以转换为 CQ 码
        cq_message = self._convert_to_cq(message.content)
        message.content = cq_message
        return await self.send_message(message, reply_to)

    async def send_image(
        self,
        message: ChannelMessage,
        image_url: str
    ) -> bool:
        """发送图片消息"""
        if not self._connected or not self._http_client:
            return False

        try:

            url = f"http://{self._http_host}:{self._http_port}/send_private_msg"
            # CQ 码格式发送图片
            cq_image = f"[CQ:image,file={image_url}]"
            data = {
                "user_id": int(message.user_id),
                "message": cq_image,
            }
            headers = {}
            if self._access_token:
                headers["Authorization"] = f"Bearer {self._access_token}"

            async with self._http_client.post(url, json=data, headers=headers) as resp:
                result = await resp.json()
                return result.get("status") == "ok"
        except Exception as e:
            print(f"[QQ] Image send error: {e}")
            return False

    def _convert_to_cq(self, content: str) -> str:
        """将内容转换为 CQ 码"""
        # 简单的 CQ 码转换
        # @某人
        content = content.replace("@", "[CQ:at,qq=")
        return content

    async def _handle_cqhttp_event(self, event: dict) -> None:
        """处理 CQHTTP 事件"""
        post_type = event.get("post_type")

        if post_type == "message":
            message_type = event.get("message_type")

            if message_type == "private":
                channel_message = ChannelMessage(
                    id=str(event.get("message_id", uuid.uuid4().int)),
                    role=MessageRole.USER,
                    content=event.get("raw_message", ""),
                    platform=self.platform,
                    channel_id=str(event.get("group_id", "")),
                    user_id=str(event.get("user_id", "")),
                    metadata={
                        "nickname": event.get("sender", {}).get("nickname", ""),
                    },
                )
                await self._notify_handler(channel_message)

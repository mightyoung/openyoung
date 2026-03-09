"""
Feishu Channel - 飞书平台适配器

基于飞书开放平台 API 实现
"""

import time
from typing import Any

from .base import BaseChannel, ChannelMessage


class FeishuChannel(BaseChannel):
    """飞书通道适配器

    支持:
    1. 机器人消息推送
    2. 事件回调接收

    配置参数:
    - app_id: 飞书应用 ID
    - app_secret: 飞书应用密钥
    - webhook_url: Webhook 地址 (可选)
    """

    def __init__(self, config: dict[str, Any] = None):
        super().__init__(config)
        self._app_id = self.config.get("app_id", "")
        self._app_secret = self.config.get("app_secret", "")
        self._webhook_url = self.config.get("webhook_url", "")
        self._tenant_access_token = None
        self._token_expires_at = 0

    @property
    def platform(self) -> str:
        return "feishu"

    async def connect(self) -> bool:
        """连接到飞书"""
        if not self._app_id or not self._app_secret:
            print("[Feishu] No app_id or app_secret configured")
            return False

        try:
            # 获取 tenant_access_token
            await self._refresh_token()
            self._connected = True
            print(f"[Feishu] Connected (app_id: ...{self._app_id[-4:]})")
            return True
        except Exception as e:
            print(f"[Feishu] Connection failed: {e}")
            return False

    async def disconnect(self) -> bool:
        """断开连接"""
        self._tenant_access_token = None
        self._connected = False
        print("[Feishu] Disconnected")
        return True

    async def _refresh_token(self) -> str:
        """刷新 tenant_access_token"""
        current_time = time.time()

        # 如果 token 有效，直接返回
        if self._tenant_access_token and current_time < self._token_expires_at:
            return self._tenant_access_token

        try:
            import aiohttp

            url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
            data = {
                "app_id": self._app_id,
                "app_secret": self._app_secret,
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=data) as resp:
                    result = await resp.json()

                    if result.get("code") == 0:
                        self._tenant_access_token = result["tenant_access_token"]
                        # 提前 5 分钟过期
                        self._token_expires_at = current_time + result.get("expire", 7200) - 300
                        return self._tenant_access_token
                    else:
                        raise Exception(f"Token failed: {result}")
        except Exception as e:
            print(f"[Feishu] Token refresh failed: {e}")
            raise

    async def send_message(self, message: ChannelMessage, reply_to: str | None = None) -> bool:
        """发送文本消息到飞书"""
        if not self._connected:
            return False

        try:
            import aiohttp

            # 获取 token
            token = await self._refresh_token()

            # 构建消息体
            url = "https://open.feishu.cn/open-apis/im/v1/messages"
            params = {"receive_id_type": "user_id"}
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json; charset=utf-8",
            }

            data = {
                "receive_id": message.user_id,
                "msg_type": "text",
                "content": json.dumps({"text": message.content}),
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=data, params=params, headers=headers) as resp:
                    result = await resp.json()
                    if result.get("code") == 0 or result.get("msg_id"):
                        print(f"[Feishu] Sent message to {message.user_id}")
                        return True
                    else:
                        print(f"[Feishu] Send failed: {result}")
                        return False
        except Exception as e:
            print(f"[Feishu] Send error: {e}")
            return False

    async def send_markdown(self, message: ChannelMessage, reply_to: str | None = None) -> bool:
        """发送 Markdown 消息"""
        if not self._connected:
            return False

        try:
            import json

            import aiohttp

            token = await self._refresh_token()

            url = "https://open.feishu.cn/open-apis/im/v1/messages"
            params = {"receive_id_type": "user_id"}
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json; charset=utf-8",
            }

            # 飞书使用 post 消息类型支持富文本
            data = {
                "receive_id": message.user_id,
                "msg_type": "post",
                "content": json.dumps(
                    {
                        "post": {
                            "zh_cn": {
                                "title": "OpenYoung",
                                "content": [[{"tag": "text", "text": message.content}]],
                            }
                        }
                    }
                ),
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=data, params=params, headers=headers) as resp:
                    result = await resp.json()
                    return result.get("code") == 0 or result.get("msg_id") is not None
        except Exception as e:
            print(f"[Feishu] Markdown send error: {e}")
            return False

    async def send_image(self, message: ChannelMessage, image_url: str) -> bool:
        """发送图片消息"""
        if not self._connected:
            return False

        try:
            # 飞书发送图片需要先上传图片
            print("[Feishu] Image upload not implemented")
            return False
        except Exception as e:
            print(f"[Feishu] Image send error: {e}")
            return False


class FeishuWebhookChannel(FeishuChannel):
    """飞书 Webhook 模式适配器

    简化模式，使用 Webhook URL 发送消息
    """

    def __init__(self, config: dict[str, Any] = None):
        super().__init__(config)
        self._webhook_url = self.config.get("webhook_url", "")

    async def connect(self) -> bool:
        """验证 Webhook"""
        if not self._webhook_url:
            print("[Feishu] No webhook URL configured")
            return False

        self._connected = True
        print("[Feishu] Webhook mode configured")
        return True

    async def send_message(self, message: ChannelMessage, reply_to: str | None = None) -> bool:
        """通过 Webhook 发送消息"""
        if not self._connected:
            return False

        try:
            import aiohttp

            # Webhook 消息格式
            data = {"msg_type": "text", "content": {"text": message.content}}

            async with aiohttp.ClientSession() as session:
                async with session.post(self._webhook_url, json=data) as resp:
                    return resp.status == 200
        except Exception as e:
            print(f"[Feishu] Webhook send error: {e}")
            return False


import json

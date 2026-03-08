"""
DingTalk Channel - 钉钉平台适配器

基于钉钉 Webhook 实现
"""

import base64
import hashlib
import hmac
import urllib.parse
from typing import Any

from .base import BaseChannel, ChannelMessage


class DingTalkChannel(BaseChannel):
    """钉钉通道适配器

    支持两种模式:
    1. Webhook 模式 (简单)
    2. 企业机器人模式 (需要签名)

    配置参数:
    - webhook_url: Webhook 地址
    - secret: 签名密钥 (可选，开启签名验证时需要)
    """

    def __init__(self, config: dict[str, Any] = None):
        super().__init__(config)
        self._webhook_url = self.config.get("webhook_url", "")
        self._secret = self.config.get("secret", "")

    @property
    def platform(self) -> str:
        return "dingtalk"

    async def connect(self) -> bool:
        """连接钉钉 (验证 Webhook)"""
        if not self._webhook_url:
            print("[DingTalk] No webhook URL configured")
            return False

        try:
            # 简单验证：检查 URL 格式
            if not self._webhook_url.startswith("https://"):
                print("[DingTalk] Webhook URL must use HTTPS")
                return False

            self._connected = True
            print("[DingTalk] Configured with webhook")
            return True
        except Exception as e:
            print(f"[DingTalk] Connection failed: {e}")
            return False

    async def disconnect(self) -> bool:
        """断开连接"""
        self._connected = False
        print("[DingTalk] Disconnected")
        return True

    async def send_message(
        self,
        message: ChannelMessage,
        reply_to: str | None = None
    ) -> bool:
        """发送文本消息到钉钉"""
        if not self._connected:
            return False

        try:
            import aiohttp

            # 构建消息体 (钉钉 Markdown 格式)
            msg_body = {
                "msgtype": "text",
                "text": {
                    "content": message.content
                }
            }

            async with aiohttp.ClientSession() as session:
                # 如果有签名密钥，使用签名
                if self._secret:
                    url, timestamp, sign = self._generate_sign()
                    final_url = f"{url}&timestamp={timestamp}&sign={sign}"
                else:
                    final_url = self._webhook_url

                async with session.post(final_url, json=msg_body) as resp:
                    result = await resp.json()
                    if result.get("errcode") == 0:
                        print("[DingTalk] Sent message")
                        return True
                    else:
                        print(f"[DingTalk] Send failed: {result}")
                        return False
        except Exception as e:
            print(f"[DingTalk] Send error: {e}")
            return False

    async def send_markdown(
        self,
        message: ChannelMessage,
        reply_to: str | None = None
    ) -> bool:
        """发送 Markdown 消息"""
        if not self._connected:
            return False

        try:
            import aiohttp

            # 钉钉 Markdown 格式
            msg_body = {
                "msgtype": "markdown",
                "markdown": {
                    "title": "OpenYoung",
                    "text": message.content
                }
            }

            async with aiohttp.ClientSession() as session:
                if self._secret:
                    url, timestamp, sign = self._generate_sign()
                    final_url = f"{url}&timestamp={timestamp}&sign={sign}"
                else:
                    final_url = self._webhook_url

                async with session.post(final_url, json=msg_body) as resp:
                    result = await resp.json()
                    return result.get("errcode") == 0
        except Exception as e:
            print(f"[DingTalk] Markdown send error: {e}")
            return False

    async def send_image(
        self,
        message: ChannelMessage,
        image_url: str
    ) -> bool:
        """发送图片消息 (需要图片 ID)"""
        if not self._connected:
            return False

        # 钉钉不支持直接通过 URL 发送图片
        # 需要先上传图片获取 media_id
        print("[DingTalk] Image upload not implemented")
        return False

    def _generate_sign(self) -> tuple:
        """生成签名

        Returns:
            (webhook_url, timestamp, sign)
        """
        import time

        timestamp = str(round(time.time() * 1000))
        secret_enc = self._secret.encode('utf-8')
        string_to_sign = f'{timestamp}\n{self._secret}'
        string_to_sign_enc = string_to_sign.encode('utf-8')
        hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
        sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))

        # 解析原始 URL，去除签名参数
        base_url = self._webhook_url.split('&sign=')[0]

        return base_url, timestamp, sign


class DingTalkCallbackChannel(DingTalkChannel):
    """钉钉回调模式适配器

    用于接收钉钉服务器推送的事件
    """

    def __init__(self, config: dict[str, Any] = None):
        super().__init__(config)
        self._callback_token = self.config.get("callback_token", "")
        self._callback_encrypt_key = self.config.get("callback_encrypt_key", "")

    async def connect(self) -> bool:
        """启动回调服务器"""
        # 实际需要启动一个 HTTP 服务器来接收回调
        print("[DingTalk] Callback mode requires HTTP server")
        return False

    async def _verify_callback(self, timestamp: str, signature: str) -> bool:
        """验证回调签名"""
        if not self._callback_token:
            return True

        string_to_sign = f"{timestamp}\n{self._callback_token}"
        import base64
        import hashlib
        import hmac

        hmac_code = hmac.new(
            self._callback_token.encode('utf-8'),
            string_to_sign.encode('utf-8'),
            digestmod=hashlib.sha256
        ).digest()
        expected_sign = base64.b64encode(hmac_code).decode('utf-8')

        return signature == expected_sign

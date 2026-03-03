"""
LLM Client - 使用 .env 中的 API keys
支持 tool calling
"""

import json
import os
import httpx
from typing import Optional, List, Dict, Any

# 尝试加载 dotenv
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass


class LLMClient:
    """简单的 LLM 客户端，支持多种 Provider 和 tool calling"""

    PROVIDERS = {
        "deepseek": {
            "prefix": ["deepseek-chat", "deepseek-coder", "deepseek-reasoner"],
            "base_url": "https://api.deepseek.com",
            "env_key": "DEEPSEEK_CONFIG",
        },
        "moonshot": {
            "prefix": [
                "moonshot-v1-8k",
                "moonshot-v1-32k",
                "moonshot-v1-128k",
                "kimi-k2.5",
            ],
            "base_url": "https://api.moonshot.cn/v1",
            "env_key": "MOONSHOT_CONFIG",
        },
        "qwen": {
            "prefix": ["qwen-plus", "qwen-turbo", "qwen-max", "qwen-max-longcontext"],
            "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "env_key": "QWEN_CONFIG",
        },
        "glm": {
            "prefix": ["glm-5", "glm-4", "glm-4-flash", "glm-4.7"],
            "base_url": "https://open.bigmodel.cn/api/paas/v4",
            "env_key": "GLM_CONFIG",
        },
    }

    def __init__(self):
        self._client = httpx.AsyncClient(timeout=120.0)
        self._configs = self._load_configs()

    def _load_configs(self) -> Dict[str, Dict[str, Any]]:
        configs = {}
        for name, info in self.PROVIDERS.items():
            config_str = os.getenv(info["env_key"])
            if config_str:
                try:
                    configs[name] = json.loads(config_str)
                except json.JSONDecodeError:
                    pass
        return configs

    def _find_provider(self, model: str) -> Optional[tuple]:
        for name, config in self._configs.items():
            prefixes = config.get("prefix", [])
            for prefix in prefixes:
                if model.startswith(prefix) or model in prefixes:
                    return (name, config)
        return None

    async def chat(
        self,
        model: str,
        messages: List[Dict[str, Any]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        tools: Optional[List[Dict]] = None,
    ) -> Dict[str, Any]:
        provider_info = self._find_provider(model)

        if not provider_info:
            provider_info = ("deepseek", self._configs.get("deepseek"))

        if not provider_info or not provider_info[1]:
            raise ValueError(f"No valid config found for model: {model}")

        name, config = provider_info
        base_url = config["base_url"]
        api_key = config["api_key"]

        url = f"{base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
        }

        if max_tokens:
            payload["max_tokens"] = max_tokens

        if tools:
            payload["tools"] = tools

        response = await self._client.post(url, headers=headers, json=payload)
        response.raise_for_status()

        result = response.json()
        return result

    async def chat_text(
        self,
        model: str,
        messages: List[Dict[str, Any]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        tools: Optional[List[Dict]] = None,
    ) -> str:
        result = await self.chat(model, messages, temperature, max_tokens, tools)
        return result["choices"][0]["message"]["content"]

    async def close(self):
        await self._client.aclose()


async def test_llm():
    client = LLMClient()
    print("可用 Providers:", list(client._configs.keys()))
    if not client._configs:
        print("错误: 没有找到有效的 LLM 配置")
        return
    provider_name = list(client._configs.keys())[0]
    config = client._configs[provider_name]
    model = config["prefix"][0]
    print(f"使用 Provider: {provider_name}, 模型: {model}")
    messages = [
        {"role": "system", "content": "你是一个有帮助的AI助手。"},
        {"role": "user", "content": "你好！"},
    ]
    try:
        response = await client.chat(model, messages)
        print("响应:", response["choices"][0]["message"]["content"])
    except Exception as e:
        print("错误:", e)
    await client.close()


if __name__ == "__main__":
    import asyncio

    asyncio.run(test_llm())

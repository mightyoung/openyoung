"""
PackageManager Provider - LLM Provider 管理
"""

import os
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime


class ProviderManager:
    """LLM Provider 管理器"""

    # Provider 类型映射
    PROVIDER_CONFIGS = {
        "deepseek": {
            "prefix": ["deepseek-chat", "deepseek-coder", "deepseek-reasoner"],
            "base_url": "https://api.deepseek.com",
            "env_key": "DEEPSEEK_CONFIG",
            "api_key_env": "DEEPSEEK_API_KEY",
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
            "api_key_env": "MOONSHOT_API_KEY",
        },
        "qwen": {
            "prefix": ["qwen-plus", "qwen-turbo", "qwen-max", "qwen-max-longcontext"],
            "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "env_key": "QWEN_CONFIG",
            "api_key_env": "DASHSCOPE_API_KEY",
        },
        "glm": {
            "prefix": ["glm-5", "glm-4", "glm-4-flash", "glm-4.7"],
            "base_url": "https://open.bigmodel.cn/api/paas/v4",
            "env_key": "GLM_CONFIG",
            "api_key_env": "ZHIPU_API_KEY",
        },
        "openai": {
            "prefix": ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"],
            "base_url": "https://api.openai.com/v1",
            "env_key": "OPENAI_CONFIG",
            "api_key_env": "OPENAI_API_KEY",
        },
    }

    def __init__(self, storage=None):
        self.storage = storage

    @property
    def available_providers(self) -> List[str]:
        """获取可用的 Provider 类型"""
        return list(self.PROVIDER_CONFIGS.keys())

    def get_provider_info(self, provider_type: str) -> Optional[Dict]:
        """获取 Provider 配置信息"""
        return self.PROVIDER_CONFIGS.get(provider_type)

    def get_models_for_provider(self, provider_type: str) -> List[str]:
        """获取 Provider 支持的模型列表"""
        info = self.get_provider_info(provider_type)
        return info["prefix"] if info else []

    def detect_provider_type(self, model: str) -> Optional[str]:
        """根据模型名检测 Provider 类型"""
        for provider_type, config in self.PROVIDER_CONFIGS.items():
            for prefix in config["prefix"]:
                if model.startswith(prefix) or model == prefix:
                    return provider_type
        return None

    def get_api_key_from_env(self, provider_type: str) -> Optional[str]:
        """从环境变量获取 API Key"""
        info = self.PROVIDER_CONFIGS.get(provider_type)
        if not info:
            return None

        # 先尝试从 JSON 配置获取
        import json

        config_str = os.getenv(info["env_key"])
        if config_str:
            try:
                config = json.loads(config_str)
                return config.get("api_key")
            except (json.JSONDecodeError, TypeError):
                pass

        # 再尝试从独立的 API Key 环境变量获取
        return os.getenv(info.get("api_key_env"))

    def get_base_url(self, provider_type: str) -> Optional[str]:
        """获取 Provider 的 Base URL"""
        info = self.PROVIDER_CONFIGS.get(provider_type)

        if info:
            # 先尝试从 JSON 配置获取
            import json

            config_str = os.getenv(info["env_key"])
            if config_str:
                try:
                    config = json.loads(config_str)
                    return config.get("base_url")
                except (json.JSONDecodeError, TypeError):
                    pass

            return info.get("base_url")
        return None

    def validate_provider_config(self, provider_type: str, api_key: str) -> bool:
        """验证 Provider 配置是否有效"""
        # 基本验证：非空
        if not api_key or not api_key.strip():
            return False

        # 检查是否为有效格式
        if provider_type == "openai":
            return api_key.startswith("sk-")
        elif provider_type == "deepseek":
            return api_key.startswith("sk-")
        elif provider_type == "moonshot":
            return api_key.startswith("sk-")
        elif provider_type == "qwen":
            return api_key.startswith("sk-")
        elif provider_type == "glm":
            return len(api_key) > 10

        return True

    def create_provider_from_env(self, provider_type: str) -> Optional[Dict]:
        """从环境变量创建 Provider 配置"""
        info = self.PROVIDER_CONFIGS.get(provider_type)
        if not info:
            return None

        import json

        config_str = os.getenv(info["env_key"])

        if config_str:
            try:
                config = json.loads(config_str)
                return {
                    "name": provider_type,
                    "provider_type": provider_type,
                    "base_url": config.get("base_url", info["base_url"]),
                    "api_key": config.get("api_key"),
                    "models": info["prefix"],
                    "enabled": True,
                }
            except (json.JSONDecodeError, TypeError):
                pass

        # 尝试从独立环境变量获取
        api_key = os.getenv(info.get("api_key_env"))
        if api_key:
            return {
                "name": provider_type,
                "provider_type": provider_type,
                "base_url": info["base_url"],
                "api_key": api_key,
                "models": info["prefix"],
                "enabled": True,
            }

        return None

    def load_all_from_env(self) -> List[Dict]:
        """从环境变量加载所有已配置的 Providers"""
        providers = []

        for provider_type in self.available_providers:
            config = self.create_provider_from_env(provider_type)
            if config:
                providers.append(config)

        return providers

    def get_provider_for_model(self, model: str) -> Optional[Dict]:
        """根据模型获取 Provider 配置"""
        # 先尝试从存储中获取
        if self.storage:
            providers = self.storage.list_providers(enabled_only=True)
            for p in providers:
                if model in p.models:
                    return {
                        "name": p.name,
                        "provider_type": p.provider_type,
                        "base_url": p.base_url,
                        "api_key": p.api_key,
                        "model": model,
                    }

        # 再尝试从环境变量检测
        provider_type = self.detect_provider_type(model)
        if provider_type:
            return self.create_provider_from_env(provider_type)

        return None

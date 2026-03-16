"""
Hub Integration - Hub 集成模块

提供 Hub 功能与 Core 模块的统一集成接口
"""

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


class HubIntegration:
    """Hub 集成器

    统一 Hub 功能与 Core 模块的接口
    """

    def __init__(self):
        self._registry = None
        self._evaluator = None
        self._retriever = None
        self._hooks = None

    def set_registry(self, registry):
        """设置注册表"""
        self._registry = registry

    def set_evaluator(self, evaluator):
        """设置评估器"""
        self._evaluator = evaluator

    def set_retriever(self, retriever):
        """设置检索器"""
        self._retriever = retriever

    def set_hooks(self, hooks):
        """设置 Hooks"""
        self._hooks = hooks

    async def discover(self, query: str) -> list[Any]:
        """发现 Agent"""
        if self._retriever:
            return await self._retriever.retrieve(query)
        return []

    async def evaluate(self, agent_id: str, task: str) -> dict[str, Any]:
        """评估 Agent"""
        if self._evaluator:
            return await self._evaluator.evaluate(agent_id, task)
        return {}

    async def register(self, agent_spec: Any) -> bool:
        """注册 Agent"""
        if self._registry:
            return await self._registry.register(agent_spec)
        return False

    def get_capabilities(self) -> dict[str, bool]:
        """获取可用功能"""
        return {
            "registry": self._registry is not None,
            "evaluator": self._evaluator is not None,
            "retriever": self._retriever is not None,
            "hooks": self._hooks is not None,
        }


# Singleton instance
_hub_integration: Optional[HubIntegration] = None


def get_hub_integration() -> HubIntegration:
    """获取 Hub 集成器单例"""
    global _hub_integration
    if _hub_integration is None:
        _hub_integration = HubIntegration()
    return _hub_integration

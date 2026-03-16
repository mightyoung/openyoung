"""
Registry Adapter - 注册表适配器

将 package_manager 的注册表适配到新的 core.registry
实现统一的注册表接口
"""

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


class RegistryAdapter:
    """注册表适配器

    适配旧的 package_manager 注册表到新的 core.registry
    """

    def __init__(self, core_registry=None):
        self._core_registry = core_registry
        self._legacy_registry = None

    def set_core_registry(self, registry):
        """设置核心注册表"""
        self._core_registry = registry

    def set_legacy_registry(self, registry):
        """设置旧注册表"""
        self._legacy_registry = registry

    async def get(self, key: str, default: Any = None) -> Any:
        """获取值"""
        # 优先从核心注册表获取
        if self._core_registry:
            try:
                return await self._core_registry.get(key)
            except Exception as e:
                logger.debug(f"Core registry get failed: {e}")

        # 回退到旧注册表
        if self._legacy_registry:
            try:
                return self._legacy_registry.get(key)
            except Exception as e:
                logger.debug(f"Legacy registry get failed: {e}")

        return default

    async def set(self, key: str, value: Any):
        """设置值"""
        # 优先设置到核心注册表
        if self._core_registry:
            try:
                await self._core_registry.set(key, value)
                return
            except Exception as e:
                logger.warning(f"Core registry set failed: {e}")

        # 回退到旧注册表
        if self._legacy_registry:
            try:
                self._legacy_registry.set(key, value)
                return
            except Exception as e:
                logger.warning(f"Legacy registry set failed: {e}")

    async def delete(self, key: str):
        """删除值"""
        if self._core_registry:
            try:
                await self._core_registry.delete(key)
            except Exception as e:
                logger.warning(f"Core registry delete failed: {e}")

        if self._legacy_registry:
            try:
                self._legacy_registry.delete(key)
            except Exception as e:
                logger.warning(f"Legacy registry delete failed: {e}")

    async def list_keys(self, pattern: str = "*") -> list[str]:
        """列出匹配的键"""
        keys = set()

        if self._core_registry:
            try:
                core_keys = await self._core_registry.list_keys(pattern)
                keys.update(core_keys)
            except Exception as e:
                logger.debug(f"Core registry list failed: {e}")

        if self._legacy_registry:
            try:
                legacy_keys = self._legacy_registry.list_keys(pattern)
                keys.update(legacy_keys)
            except Exception as e:
                logger.debug(f"Legacy registry list failed: {e}")

        return sorted(keys)


# Singleton instance
_registry_adapter: Optional[RegistryAdapter] = None


def get_registry_adapter() -> RegistryAdapter:
    """获取注册表适配器单例"""
    global _registry_adapter
    if _registry_adapter is None:
        _registry_adapter = RegistryAdapter()
    return _registry_adapter

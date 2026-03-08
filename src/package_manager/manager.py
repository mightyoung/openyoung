"""
PackageManager - 包管理系统
"""

from datetime import datetime
from typing import Any

from .provider import ProviderManager
from .storage import LLMProviderConfig, LockManager, PackageMetadata, PackageStorage


class PackageManager:
    """包管理器 - 安装和管理依赖包"""

    def __init__(self, package_dir: str | None = None):
        # 初始化存储
        if package_dir:
            self.storage = PackageStorage(package_dir)
        else:
            # 默认使用 .mightyoung 目录
            self.storage = PackageStorage()

        # 初始化 Provider 管理器
        self.provider_manager = ProviderManager(self.storage)

        # 初始化 Lock 管理器
        self.lock_manager = LockManager(self.storage)

        # 从环境变量加载已配置的 Providers
        self._load_providers_from_env()

    def _load_providers_from_env(self):
        """从环境变量加载已配置的 Providers"""
        env_providers = self.provider_manager.load_all_from_env()

        # 检查是否已存在，不存在则添加
        existing = self.storage.list_providers()
        existing_names = {p.name for p in existing}

        for cfg in env_providers:
            if cfg["name"] not in existing_names:
                provider = LLMProviderConfig(**cfg)
                self.storage.add_provider(provider)

    # ========== Package Operations ==========

    async def install(
        self,
        package_name: str,
        version: str | None = None,
        package_type: str = "skill",
        description: str = "",
        entry: str = "",
    ) -> bool:
        """安装包"""
        package = PackageMetadata(
            name=package_name,
            version=version or "1.0.0",
            package_type=package_type,
            description=description,
            entry=entry,
            source="local",
            installed_at=datetime.now().isoformat(),
        )

        self.storage.add_package(package)

        # 重新生成 lock 文件
        self.regenerate_lock()

        return True

    async def uninstall(self, package_name: str) -> bool:
        """卸载包"""
        result = self.storage.remove_package(package_name)

        if result:
            self.regenerate_lock()

        return result

    def list_packages(self, package_type: str | None = None) -> list[PackageMetadata]:
        """列出已安装的包"""
        return self.storage.list_packages(package_type)

    def get_package(self, name: str) -> PackageMetadata | None:
        """获取包信息"""
        return self.storage.get_package(name)

    def regenerate_lock(self):
        """重新生成 lock 文件"""
        packages = self.storage.load_registry()
        self.lock_manager.generate_lock(packages)

    # ========== LLM Provider Operations ==========

    def add_provider(
        self,
        name: str,
        provider_type: str,
        base_url: str,
        api_key: str,
        models: list[str] | None = None,
    ) -> bool:
        """添加 LLM Provider"""
        # 验证配置
        if not self.provider_manager.validate_provider_config(provider_type, api_key):
            return False

        provider = LLMProviderConfig(
            name=name,
            provider_type=provider_type,
            base_url=base_url,
            api_key=api_key,
            models=models or self.provider_manager.get_models_for_provider(provider_type),
        )

        self.storage.add_provider(provider)
        return True

    def remove_provider(self, name: str) -> bool:
        """移除 LLM Provider"""
        return self.storage.remove_provider(name)

    def get_provider(self, name: str) -> LLMProviderConfig | None:
        """获取 LLM Provider"""
        return self.storage.get_provider(name)

    def list_providers(self, enabled_only: bool = False) -> list[LLMProviderConfig]:
        """列出 LLM Providers"""
        return self.storage.list_providers(enabled_only)

    def set_default_provider(self, name: str) -> None:
        """设置默认 Provider"""
        self.storage.set_default_provider(name)

    def get_default_provider(self) -> LLMProviderConfig | None:
        """获取默认 Provider"""
        return self.storage.get_default_provider()

    def get_provider_for_model(self, model: str) -> dict | None:
        """根据模型获取 Provider 配置"""
        return self.provider_manager.get_provider_for_model(model)

    # ========== Source Operations ==========

    def load_sources(self) -> dict[str, Any]:
        """加载 Source 配置"""
        if not self.storage.sources_file.exists():
            return {"sources": []}

        import yaml

        with open(self.storage.sources_file, encoding="utf-8") as f:
            return yaml.safe_load(f) or {"sources": []}

    def save_sources(self, sources: dict[str, Any]) -> None:
        """保存 Source 配置"""
        import yaml

        with open(self.storage.sources_file, "w", encoding="utf-8") as f:
            yaml.dump(sources, f, default_flow_style=False)

    # ========== Lock Operations ==========

    def load_lock(self) -> dict[str, Any]:
        """加载 lock 文件"""
        return self.lock_manager.load_lock()

    def save_lock(self, lock_data: dict[str, Any]) -> None:
        """保存 lock 文件"""
        self.lock_manager.save_lock(lock_data)

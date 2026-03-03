"""
PackageManager Storage - 持久化存储层
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict


@dataclass
class PackageMetadata:
    """包元数据"""

    name: str
    version: str
    package_type: str  # skill, mcp, evaluation, dataset, capsule, hybrid
    description: str = ""
    entry: str = ""
    dependencies: List[str] = None
    checksum: str = ""
    source: str = "local"  # local, github, npm
    installed_at: str = ""

    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []


@dataclass
class LLMProviderConfig:
    """LLM Provider 配置"""

    name: str
    provider_type: str  # deepseek, moonshot, qwen, glm, openai
    base_url: str
    api_key: str
    models: List[str] = None
    enabled: bool = True

    def __post_init__(self):
        if self.models is None:
            self.models = []


class PackageStorage:
    """包存储管理器 - 负责持久化"""

    DEFAULT_DIR = ".mightyoung"

    def __init__(self, base_dir: Optional[str] = None):
        self.base_dir = Path(base_dir) if base_dir else Path.cwd() / self.DEFAULT_DIR
        self._ensure_dirs()

    def _ensure_dirs(self):
        """确保目录结构存在"""
        dirs = [
            self.base_dir,
            self.base_dir / "packages",
            self.base_dir / "evolved",
            self.base_dir / "cache",
            self.base_dir / "locks",
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)

    @property
    def registry_file(self) -> Path:
        return self.base_dir / "registry.json"

    @property
    def providers_file(self) -> Path:
        return self.base_dir / "providers.json"

    @property
    def sources_file(self) -> Path:
        return self.base_dir / "sources.yaml"

    @property
    def lock_file(self) -> Path:
        return self.base_dir / "lock.yaml"

    # ========== Registry Operations ==========

    def load_registry(self) -> Dict[str, PackageMetadata]:
        """加载注册表"""
        if not self.registry_file.exists():
            return {}

        with open(self.registry_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        result = {}
        for name, pkg_data in data.items():
            result[name] = PackageMetadata(**pkg_data)
        return result

    def save_registry(self, registry: Dict[str, PackageMetadata]) -> None:
        """保存注册表"""
        data = {name: asdict(pkg) for name, pkg in registry.items()}
        with open(self.registry_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def add_package(self, package: PackageMetadata) -> None:
        """添加包到注册表"""
        registry = self.load_registry()
        registry[package.name] = package
        self.save_registry(registry)

    def remove_package(self, name: str) -> bool:
        """从注册表移除包"""
        registry = self.load_registry()
        if name in registry:
            del registry[name]
            self.save_registry(registry)
            return True
        return False

    def get_package(self, name: str) -> Optional[PackageMetadata]:
        """获取包"""
        registry = self.load_registry()
        return registry.get(name)

    def list_packages(
        self, package_type: Optional[str] = None
    ) -> List[PackageMetadata]:
        """列出包"""
        registry = self.load_registry()
        packages = list(registry.values())

        if package_type:
            packages = [p for p in packages if p.package_type == package_type]

        return packages

    # ========== LLM Provider Operations ==========

    def load_providers(self) -> Dict[str, LLMProviderConfig]:
        """加载 LLM Provider 配置"""
        if not self.providers_file.exists():
            return {}

        with open(self.providers_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        result = {}
        for name, cfg_data in data.items():
            result[name] = LLMProviderConfig(**cfg_data)
        return result

    def save_providers(self, providers: Dict[str, LLMProviderConfig]) -> None:
        """保存 LLM Provider 配置"""
        data = {name: asdict(cfg) for name, cfg in providers.items()}
        with open(self.providers_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def add_provider(self, provider: LLMProviderConfig) -> None:
        """添加 LLM Provider"""
        providers = self.load_providers()
        providers[provider.name] = provider
        self.save_providers(providers)

    def remove_provider(self, name: str) -> bool:
        """移除 LLM Provider"""
        providers = self.load_providers()
        if name in providers:
            del providers[name]
            self.save_providers(providers)
            return True
        return False

    def get_provider(self, name: str) -> Optional[LLMProviderConfig]:
        """获取 LLM Provider"""
        providers = self.load_providers()
        return providers.get(name)

    def list_providers(self, enabled_only: bool = False) -> List[LLMProviderConfig]:
        """列出 LLM Providers"""
        providers = self.load_providers()
        result = list(providers.values())

        if enabled_only:
            result = [p for p in result if p.enabled]

        return result

    def set_default_provider(self, name: str) -> None:
        """设置默认 Provider"""
        providers = self.load_providers()

        # 先禁用所有
        for p in providers.values():
            p.enabled = False

        # 启用指定的
        if name in providers:
            providers[name].enabled = True

        self.save_providers(providers)

    def get_default_provider(self) -> Optional[LLMProviderConfig]:
        """获取默认 Provider"""
        providers = self.load_providers()
        for p in providers.values():
            if p.enabled:
                return p
        return None


class LockManager:
    """Lock 文件管理器"""

    def __init__(self, storage: PackageStorage):
        self.storage = storage

    def load_lock(self) -> Dict[str, Any]:
        """加载 lock 文件"""
        if not self.storage.lock_file.exists():
            return {}

        import yaml

        with open(self.storage.lock_file, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    def save_lock(self, lock_data: Dict[str, Any]) -> None:
        """保存 lock 文件"""
        import yaml

        with open(self.storage.lock_file, "w", encoding="utf-8") as f:
            yaml.dump(lock_data, f, default_flow_style=False)

    def generate_lock(self, packages: Dict[str, PackageMetadata]) -> None:
        """生成 lock 文件"""
        from datetime import datetime

        lock_data = {
            "version": "1.0",
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "generator": "openyoung/1.0.0",
            },
            "packages": {},
        }

        for name, pkg in packages.items():
            lock_data["packages"][name] = {
                "version": pkg.version,
                "source": pkg.source,
                "checksum": pkg.checksum,
                "dependencies": pkg.dependencies,
            }

        self.save_lock(lock_data)

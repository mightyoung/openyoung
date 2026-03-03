"""
Hooks Configuration Loader
Hooks 配置加载器
"""

import json
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum


class HookTrigger(str, Enum):
    """Hook 触发时机"""
    SESSION_START = "session_start"
    SESSION_END = "session_end"
    PRE_TASK = "pre_task"
    POST_TASK = "post_task"
    PRE_EDIT = "pre-edit"
    POST_EDIT = "post-edit"


class HookAction(str, Enum):
    """Hook 动作"""
    MEMORY_STORE = "memory_store"
    MEMORY_LOAD = "memory_load"
    CONTEXT_LOAD = "context_load"
    METRICS_COLLECT = "metrics_collect"


@dataclass
class HookConfig:
    """Hook 配置"""
    name: str
    trigger: str
    action: str
    config: Dict[str, Any]


class HooksLoader:
    """Hooks 配置加载器"""

    def __init__(self, packages_dir: str = "packages"):
        self.packages_dir = Path(packages_dir)
        self._hooks: List[HookConfig] = []

    def discover_hooks(self) -> List[str]:
        """发现所有 Hooks 包"""
        hooks = []
        if not self.packages_dir.exists():
            return hooks

        for item in self.packages_dir.iterdir():
            if item.is_dir():
                package_yaml = item / "package.yaml"
                hooks_json = item / "hooks.json"

                if hooks_json.exists() or (package_yaml.exists() and self._is_hooks_package(package_yaml)):
                    hooks.append(item.name)

        return hooks

    def _is_hooks_package(self, package_yaml: Path) -> bool:
        """检查是否是 Hooks 包"""
        try:
            with open(package_yaml, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
                return config.get("type") == "hooks"
        except:
            return False

    def load_hooks(self, hooks_name: str = None) -> List[HookConfig]:
        """加载 Hooks 配置"""
        if hooks_name:
            return self._load_hooks_package(hooks_name)

        # 加载所有
        all_hooks = []
        for name in self.discover_hooks():
            hooks = self._load_hooks_package(name)
            all_hooks.extend(hooks)

        self._hooks = all_hooks
        return all_hooks

    def _load_hooks_package(self, hooks_name: str) -> List[HookConfig]:
        """加载指定 Hooks 包"""
        hooks_path = None

        for item in self.packages_dir.iterdir():
            if item.name == hooks_name or item.name == f"hooks-{hooks_name}":
                hooks_json = item / "hooks.json"
                if hooks_json.exists():
                    hooks_path = hooks_json
                    break

        if not hooks_path:
            # 尝试 package.yaml
            for item in self.packages_dir.iterdir():
                if item.name == hooks_name or item.name == f"hooks-{hooks_name}":
                    package_yaml = item / "package.yaml"
                    if package_yaml.exists() and self._is_hooks_package(package_yaml):
                        with open(package_yaml, "r", encoding="utf-8") as f:
                            config = yaml.safe_load(f)
                            return self._parse_hooks_config(config)

        if not hooks_path:
            print(f"[Warning] Hooks not found: {hooks_name}")
            return []

        # 加载 hooks.json
        with open(hooks_path, "r", encoding="utf-8") as f:
            config = json.load(f)

        return self._parse_hooks_config(config)

    def _parse_hooks_config(self, config: Dict) -> List[HookConfig]:
        """解析 Hooks 配置"""
        hooks = []
        hooks_list = config.get("hooks", [])

        for item in hooks_list:
            hook = HookConfig(
                name=item.get("name", ""),
                trigger=item.get("trigger", ""),
                action=item.get("action", ""),
                config=item.get("config", {}),
            )
            hooks.append(hook)

        return hooks

    def get_hooks_by_trigger(self, trigger: str) -> List[HookConfig]:
        """获取指定触发时机的 Hooks"""
        return [h for h in self._hooks if h.trigger == trigger]

    def register_hook(self, hook: HookConfig):
        """注册 Hook"""
        self._hooks.append(hook)


def load_hooks_config(hooks_name: str = None, packages_dir: str = "packages") -> List[HookConfig]:
    """加载 Hooks 配置 (CLI 入口)"""
    loader = HooksLoader(packages_dir)
    return loader.load_hooks(hooks_name)

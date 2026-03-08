"""
Hooks Configuration Loader
Hooks 配置加载器
"""

import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

import yaml


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
    EVOLVE = "evolve"  # 触发 Evolver 进化


class LearningHook:
    """自学习 Hook - 集成 Evolver

    在任务执行后自动：
    1. 收集执行数据
    2. 触发 Evolver 进化
    3. 创建 Capsule
    4. 存储学习模式
    """

    def __init__(self):
        self._evolver = None
        self._pattern_store = None

    def _get_evolver(self):
        """获取 Evolver 实例"""
        if self._evolver is None:
            try:
                from src.evolver.engine import EvolutionEngine
                self._evolver = EvolutionEngine()
            except Exception as e:
                print(f"[LearningHook] Evolver init failed: {e}")
        return self._evolver

    def on_post_task(self, context: dict) -> dict:
        """Post-task 自学习钩子"""
        evolver = self._get_evolver()
        if not evolver:
            return {"status": "evolver_not_available"}

        try:
            # 1. 提取执行信号
            signals = self._extract_signals(context)

            # 2. 触发 Evolver 进化
            gene = evolver.evolve(signals)

            # 3. 成功则创建 Capsule
            result = {}
            if gene and context.get("success"):
                capsule = evolver.create_capsule(
                    trigger=signals,
                    gene=gene,
                    summary=context.get("result_summary", ""),
                )
                result["capsule_created"] = True
                result["capsule_id"] = capsule.id if capsule else None

            # 4. 存储学习模式
            self._store_pattern(context, gene)

            result["status"] = "success"
            result["signals"] = signals
            return result

        except Exception as e:
            return {"status": "error", "error": str(e)}

    def _extract_signals(self, context: dict) -> list[str]:
        """从执行上下文提取信号"""
        signals = []

        # 基于任务类型
        task = context.get("task", "")
        task_lower = task.lower()
        if "bug" in task_lower or "fix" in task_lower:
            signals.append("repair")
        if "refactor" in task_lower or "优化" in task_lower:
            signals.append("optimize")
        if "test" in task_lower or "测试" in task_lower:
            signals.append("testing")
        if "create" in task_lower or "实现" in task_lower:
            signals.append("creation")

        # 基于执行结果
        if context.get("success"):
            signals.append("success")
        else:
            signals.append("failure")

        # 基于工具使用
        tools = context.get("tools_used", [])
        if "bash" in tools:
            signals.append("shell")
        if "write" in tools or "edit" in tools:
            signals.append("file_operation")

        return signals if signals else ["general"]

    def _store_pattern(self, context: dict, gene):
        """存储执行模式"""
        # 保存到本地文件
        try:
            import json
            from datetime import datetime

            pattern_dir = Path(".young/patterns")
            pattern_dir.mkdir(parents=True, exist_ok=True)

            pattern = {
                "task": context.get("task", ""),
                "signals": context.get("signals", []),
                "success": context.get("success", False),
                "tools_used": context.get("tools_used", []),
                "timestamp": datetime.now().isoformat(),
            }

            pattern_file = pattern_dir / "execution_patterns.json"
            patterns = []
            if pattern_file.exists():
                patterns = json.loads(pattern_file.read_text())

            patterns.append(pattern)

            # 只保留最近 100 条
            patterns = patterns[-100:]
            pattern_file.write_text(json.dumps(patterns, indent=2, ensure_ascii=False))

            print(f"[LearningHook] Stored pattern to {pattern_file}")

        except Exception as e:
            print(f"[LearningHook] Store pattern error: {e}")


@dataclass
class HookConfig:
    """Hook 配置"""
    name: str
    trigger: str
    action: str
    config: dict[str, Any]


class HooksLoader:
    """Hooks 配置加载器"""

    def __init__(self, packages_dir: str = "packages"):
        self.packages_dir = Path(packages_dir)
        self._hooks: list[HookConfig] = []

    def discover_hooks(self) -> list[str]:
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
            with open(package_yaml, encoding="utf-8") as f:
                config = yaml.safe_load(f)
                return config.get("type") == "hooks"
        except:
            return False

    def load_hooks(self, hooks_name: str = None) -> list[HookConfig]:
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

    def _load_hooks_package(self, hooks_name: str) -> list[HookConfig]:
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
                        with open(package_yaml, encoding="utf-8") as f:
                            config = yaml.safe_load(f)
                            return self._parse_hooks_config(config)

        if not hooks_path:
            print(f"[Warning] Hooks not found: {hooks_name}")
            return []

        # 加载 hooks.json
        with open(hooks_path, encoding="utf-8") as f:
            config = json.load(f)

        return self._parse_hooks_config(config)

    def _parse_hooks_config(self, config: dict) -> list[HookConfig]:
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

    def get_hooks_by_trigger(self, trigger: str) -> list[HookConfig]:
        """获取指定触发时机的 Hooks"""
        return [h for h in self._hooks if h.trigger == trigger]

    def register_hook(self, hook: HookConfig):
        """注册 Hook"""
        self._hooks.append(hook)


def load_hooks_config(hooks_name: str = None, packages_dir: str = "packages") -> list[HookConfig]:
    """加载 Hooks 配置 (CLI 入口)"""
    loader = HooksLoader(packages_dir)
    return loader.load_hooks(hooks_name)

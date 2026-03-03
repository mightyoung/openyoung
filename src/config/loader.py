"""
Config Loader - 配置文件加载器
支持 YAML 和 .env
"""

import os
import json
from pathlib import Path
from typing import Any, Dict, Optional
import yaml


class ConfigLoader:
    """配置加载器"""

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self._config: Dict[str, Any] = {}

    def load_yaml(self, filename: str) -> Dict[str, Any]:
        """加载 YAML 配置"""
        path = self.project_root / filename
        if not path.exists():
            return {}

        with open(path) as f:
            return yaml.safe_load(f) or {}

    def load_json(self, filename: str) -> Dict[str, Any]:
        """加载 JSON 配置"""
        path = self.project_root / filename
        if not path.exists():
            return {}

        with open(path) as f:
            return json.load(f)

    def load_env(self, prefix: str = "YOUNG_") -> Dict[str, str]:
        """加载环境变量"""
        return {
            key: value for key, value in os.environ.items() if key.startswith(prefix)
        }

    def merge_configs(self, *configs: Dict[str, Any]) -> Dict[str, Any]:
        """合并多个配置"""
        result = {}
        for config in configs:
            result.update(config)
        return result

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        keys = key.split(".")
        value = self._config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
        return value if value is not None else default

    def set(self, key: str, value: Any):
        """设置配置值"""
        keys = key.split(".")
        config = self._config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value

    def load_all(self, filenames: List[str] = None) -> Dict[str, Any]:
        """加载所有配置"""
        configs = []

        # 默认配置文件
        configs.append(self.load_yaml("young.yaml"))
        configs.append(self.load_yaml("young.yml"))

        # 自定义文件
        if filenames:
            for fname in filenames:
                if fname.endswith((".yaml", ".yml")):
                    configs.append(self.load_yaml(fname))
                elif fname.endswith(".json"):
                    configs.append(self.load_json(fname))

        # 环境变量
        env_config = self.load_env()
        if env_config:
            configs.append({"env": env_config})

        # 合并
        self._config = self.merge_configs(*configs)
        return self._config


from typing import List

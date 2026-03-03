"""
MCP Configuration Loader
MCP 配置加载器
"""

import json
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional


class MCPLoader:
    """MCP 配置加载器 - 支持 mcp.json 格式"""

    def __init__(self, packages_dir: str = "packages"):
        self.packages_dir = Path(packages_dir)
        self._mcp_configs: Dict[str, Dict] = {}

    def discover_mcps(self) -> List[str]:
        """发现所有 MCP 包"""
        mcps = []
        if not self.packages_dir.exists():
            return mcps

        for item in self.packages_dir.iterdir():
            if item.is_dir():
                mcp_json = item / "mcp.json"
                package_yaml = item / "package.yaml"

                if mcp_json.exists() or (package_yaml.exists() and self._is_mcp_package(package_yaml)):
                    mcps.append(item.name)

        return mcps

    def _is_mcp_package(self, package_yaml: Path) -> bool:
        """检查是否是 MCP 包"""
        try:
            with open(package_yaml, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
                return config.get("type") == "mcp"
        except:
            return False

    def load_mcp(self, mcp_name: str) -> Optional[Dict[str, Any]]:
        """加载 MCP 配置"""
        # 检查缓存
        if mcp_name in self._mcp_configs:
            return self._mcp_configs[mcp_name]

        # 查找 MCP 包
        mcp_path = None
        for item in self.packages_dir.iterdir():
            if item.name == mcp_name or item.name == f"mcp-{mcp_name}":
                mcp_json = item / "mcp.json"
                if mcp_json.exists():
                    mcp_path = mcp_json
                    break

        if not mcp_path:
            # 尝试 package.yaml 格式
            for item in self.packages_dir.iterdir():
                if item.name == mcp_name or item.name == f"mcp-{mcp_name}":
                    package_yaml = item / "package.yaml"
                    if package_yaml.exists() and self._is_mcp_package(package_yaml):
                        with open(package_yaml, "r", encoding="utf-8") as f:
                            config = yaml.safe_load(f)
                            mcp_config = self._parse_package_config(config)
                            self._mcp_configs[mcp_name] = mcp_config
                            return mcp_config

            print(f"[Warning] MCP not found: {mcp_name}")
            return None

        # 加载 mcp.json
        with open(mcp_path, "r", encoding="utf-8") as f:
            config = json.load(f)

        mcp_config = config.get("mcpServers", {})
        self._mcp_configs[mcp_name] = mcp_config
        return mcp_config

    def _parse_package_config(self, config: Dict) -> Dict[str, Any]:
        """解析 package.yaml 格式"""
        mcp_config = config.get("mcp", {})
        return {
            mcp_config.get("server_type", "local"): {
                "command": mcp_config.get("command", []),
                "env": mcp_config.get("env", {}),
            }
        }

    def get_all_mcp_configs(self) -> Dict[str, Dict]:
        """获取所有 MCP 配置"""
        mcps = self.discover_mcps()
        all_configs = {}

        for mcp_name in mcps:
            config = self.load_mcp(mcp_name)
            if config:
                all_configs[mcp_name] = config

        return all_configs


def load_mcp_config(mcp_name: str, packages_dir: str = "packages") -> Optional[Dict]:
    """加载 MCP 配置 (CLI 入口)"""
    loader = MCPLoader(packages_dir)
    return loader.load_mcp(mcp_name)

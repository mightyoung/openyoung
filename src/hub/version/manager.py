"""
Version Manager - Agent 版本管理
支持语义版本控制 (SemVer) 和版本历史追踪
"""

import re
from dataclasses import dataclass, field
from datetime import datetime


class VersionError(Exception):
    """版本相关错误"""

    pass


@dataclass
class AgentVersion:
    """单个版本"""

    version: str  # 版本号 (如 "1.2.0")
    changelog: str  # 变更日志
    released_at: str  # 发布时间
    compatible_with: str  # 兼容版本
    breaking_changes: list[str] = field(default_factory=list)

    # 解析后的版本组件
    major: int = 0
    minor: int = 0
    patch: int = 0

    def __post_init__(self):
        """解析版本号"""
        parsed = parse_semver(self.version)
        if parsed:
            self.major, self.minor, self.patch = parsed


@dataclass
class VersionHistory:
    """版本历史"""

    agent_name: str
    current_version: str = "0.0.0"
    versions: list[AgentVersion] = field(default_factory=list)

    def get_latest(self, level: str = "patch") -> AgentVersion | None:
        """获取最新版本

        Args:
            level: "major", "minor", 或 "patch"

        Returns:
            最新的版本对象
        """
        if not self.versions:
            return None

        # 按版本号排序
        sorted_versions = sorted(
            self.versions, key=lambda v: (v.major, v.minor, v.patch), reverse=True
        )

        return sorted_versions[0]

    def is_compatible(self, version: str, target: str) -> bool:
        """检查版本兼容性

        Args:
            version: 当前版本
            target: 目标版本

        Returns:
            是否兼容
        """
        v1 = parse_semver(version)
        v2 = parse_semver(target)

        if not v1 or not v2:
            return False

        # 相同主版本兼容
        return v1[0] == v2[0]


def parse_semver(version: str) -> tuple | None:
    """解析语义版本号

    Args:
        version: 版本字符串 (如 "1.2.3")

    Returns:
        (major, minor, patch) 或 None
    """
    pattern = r"^(\d+)\.(\d+)\.(\d+)$"
    match = re.match(pattern, version.strip())
    if match:
        return (int(match.group(1)), int(match.group(2)), int(match.group(3)))
    return None


def compare_versions(v1: str, v2: str) -> int:
    """比较两个版本

    Args:
        v1: 版本1
        v2: 版本2

    Returns:
        -1: v1 < v2
         0: v1 == v2
         1: v1 > v2
    """
    p1 = parse_semver(v1)
    p2 = parse_semver(v2)

    if not p1 or not p2:
        return 0

    if p1 < p2:
        return -1
    elif p1 > p2:
        return 1
    return 0


class VersionManager:
    """版本管理器"""

    def __init__(self, storage_path: str = ".young/versions"):
        from pathlib import Path

        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

    def _get_version_file(self, agent_name: str) -> Path:
        """获取版本文件路径"""
        safe_name = agent_name.replace("/", "_").replace("\\", "_")
        return self.storage_path / f"{safe_name}.json"

    def get_history(self, agent_name: str) -> VersionHistory:
        """获取版本历史

        Args:
            agent_name: Agent 名称

        Returns:
            VersionHistory 对象
        """
        import json

        version_file = self._get_version_file(agent_name)

        if not version_file.exists():
            return VersionHistory(agent_name=agent_name)

        try:
            with open(version_file) as f:
                data = json.load(f)

            versions = []
            for v in data.get("versions", []):
                versions.append(
                    AgentVersion(
                        version=v["version"],
                        changelog=v.get("changelog", ""),
                        released_at=v.get("released_at", ""),
                        compatible_with=v.get("compatible_with", ""),
                        breaking_changes=v.get("breaking_changes", []),
                    )
                )

            return VersionHistory(
                agent_name=agent_name,
                current_version=data.get("current_version", "0.0.0"),
                versions=versions,
            )
        except Exception:
            return VersionHistory(agent_name=agent_name)

    def save_history(self, history: VersionHistory) -> None:
        """保存版本历史

        Args:
            history: VersionHistory 对象
        """
        import json

        version_file = self._get_version_file(history.agent_name)

        data = {
            "agent_name": history.agent_name,
            "current_version": history.current_version,
            "versions": [
                {
                    "version": v.version,
                    "changelog": v.changelog,
                    "released_at": v.released_at,
                    "compatible_with": v.compatible_with,
                    "breaking_changes": v.breaking_changes,
                }
                for v in history.versions
            ],
        }

        with open(version_file, "w") as f:
            json.dump(data, f, indent=2)

    def register_version(
        self,
        agent_name: str,
        version: str,
        changelog: str = "",
        compatible_with: str = "*",
        breaking_changes: list[str] = None,
    ) -> AgentVersion:
        """注册新版本

        Args:
            agent_name: Agent 名称
            version: 版本号
            changelog: 变更日志
            compatible_with: 兼容版本
            breaking_changes: 重大变更列表

        Returns:
            新创建的 AgentVersion
        """
        # 验证版本号格式
        if not parse_semver(version):
            raise VersionError(f"Invalid version format: {version}")

        # 获取历史
        history = self.get_history(agent_name)

        # 检查版本是否已存在
        for v in history.versions:
            if v.version == version:
                raise VersionError(f"Version {version} already exists for {agent_name}")

        # 创建新版本
        new_version = AgentVersion(
            version=version,
            changelog=changelog,
            released_at=datetime.now().isoformat(),
            compatible_with=compatible_with,
            breaking_changes=breaking_changes or [],
        )

        # 更新历史
        history.versions.append(new_version)
        history.current_version = version

        # 保存
        self.save_history(history)

        return new_version

    def get_current_version(self, agent_name: str) -> str | None:
        """获取当前版本

        Args:
            agent_name: Agent 名称

        Returns:
            当前版本号或 None
        """
        history = self.get_history(agent_name)
        return history.current_version

    def list_versions(self, agent_name: str, limit: int = 10) -> list[AgentVersion]:
        """列出版本历史

        Args:
            agent_name: Agent 名称
            limit: 返回数量限制

        Returns:
            版本列表（按时间倒序）
        """
        history = self.get_history(agent_name)

        # 按发布时间倒序
        sorted_versions = sorted(history.versions, key=lambda v: v.released_at, reverse=True)

        return sorted_versions[:limit]

    def check_update_available(self, agent_name: str, current_version: str) -> str | None:
        """检查是否有可用更新

        Args:
            agent_name: Agent 名称
            current_version: 当前版本

        Returns:
            最新版本号或 None（无可用更新）
        """
        latest = self.get_history(agent_name).get_latest()

        if not latest:
            return None

        if compare_versions(latest.version, current_version) > 0:
            return latest.version

        return None


# ========== 便捷函数 ==========


def get_version_manager() -> VersionManager:
    """获取版本管理器实例"""
    return VersionManager()


async def get_agent_version(agent_name: str) -> str | None:
    """获取 Agent 当前版本"""
    manager = get_version_manager()
    return manager.get_current_version(agent_name)


async def list_agent_versions(agent_name: str, limit: int = 10) -> list[AgentVersion]:
    """列出 Agent 版本历史"""
    manager = get_version_manager()
    return manager.list_versions(agent_name, limit)

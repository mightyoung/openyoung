"""
Workspace Manager - Agent 工作空间隔离管理
每个导入的 Agent 有独立的工作空间
支持：创建/删除/复制/状态管理/配额控制
"""

import shutil
import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class WorkspaceStatus(str, Enum):
    """工作空间状态"""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    ARCHIVED = "archived"


@dataclass
class WorkspaceQuota:
    """工作空间配额"""
    max_storage_mb: int = 100
    max_checkpoints: int = 50
    max_traces: int = 1000
    max_sessions: int = 10


@dataclass
class WorkspaceConfig:
    """工作空间配置"""
    agent_id: str
    root_path: Path
    user_id: str = ""  # 所属用户

    # 目录结构
    memory_path: Path = None
    checkpoint_path: Path = None
    trace_path: Path = None
    output_path: Path = None
    config_path: Path = None

    # 共享配置（可选）
    shared_skills: Optional[Path] = None

    # 配额
    quota: WorkspaceQuota = field(default_factory=WorkspaceQuota)

    # 状态
    status: WorkspaceStatus = WorkspaceStatus.ACTIVE

    # 元数据
    created_at: datetime = field(default_factory=datetime.now)
    last_accessed: datetime = field(default_factory=datetime.now)
    is_active: bool = True

    # 使用统计
    storage_used_mb: float = 0.0
    checkpoint_count: int = 0
    trace_count: int = 0
    session_count: int = 0

    def __post_init__(self):
        if self.memory_path is None:
            self.memory_path = self.root_path / "memory"
        if self.checkpoint_path is None:
            self.checkpoint_path = self.root_path / "checkpoints"
        if self.trace_path is None:
            self.trace_path = self.root_path / "traces"
        if self.output_path is None:
            self.output_path = self.root_path / "output"
        if self.config_path is None:
            self.config_path = self.root_path / "config"

    def get_usage_percent(self) -> float:
        """获取存储使用百分比"""
        if self.quota.max_storage_mb == 0:
            return 0.0
        return (self.storage_used_mb / self.quota.max_storage_mb) * 100

    def can_save_checkpoint(self) -> bool:
        """是否可以保存 checkpoint"""
        return self.checkpoint_count < self.quota.max_checkpoints

    def can_save_trace(self) -> bool:
        """是否可以保存 trace"""
        return self.trace_count < self.quota.max_traces


class WorkspaceManager:
    """Agent 工作空间管理器 - 支持完整的工作空间管理"""

    def __init__(self, workspace_root: str = ".young/workspaces"):
        self.workspace_root = Path(workspace_root)
        self.workspace_root.mkdir(parents=True, exist_ok=True)

        # 内存缓存
        self._workspaces: Dict[str, WorkspaceConfig] = {}
        self._load_existing()

    def _load_existing(self):
        """加载已存在的工作空间"""
        if not self.workspace_root.exists():
            return

        for agent_dir in self.workspace_root.iterdir():
            if agent_dir.is_dir():
                agent_id = agent_dir.name
                self._workspaces[agent_id] = self._load_workspace(agent_id)

    def _load_workspace(self, agent_id: str) -> WorkspaceConfig:
        """加载工作空间配置"""
        root = self.workspace_root / agent_id

        # 读取 metadata.json 如果存在
        metadata_file = root / "metadata.json"
        quota = WorkspaceQuota()

        if metadata_file.exists():
            with open(metadata_file) as f:
                meta = json.load(f)

                # 加载配额
                if "quota" in meta:
                    quota = WorkspaceQuota(**meta["quota"])

                # 加载使用统计
                storage_used = meta.get("storage_used_mb", 0.0)
                checkpoint_count = meta.get("checkpoint_count", 0)
                trace_count = meta.get("trace_count", 0)
                session_count = meta.get("session_count", 0)

                # 加载状态
                status = WorkspaceStatus(meta.get("status", "active"))

                return WorkspaceConfig(
                    agent_id=agent_id,
                    user_id=meta.get("user_id", ""),
                    root_path=root,
                    quota=quota,
                    status=status,
                    created_at=datetime.fromisoformat(meta.get("created_at", datetime.now().isoformat())),
                    last_accessed=datetime.fromisoformat(meta.get("last_accessed", datetime.now().isoformat())),
                    is_active=meta.get("is_active", True),
                    storage_used_mb=storage_used,
                    checkpoint_count=checkpoint_count,
                    trace_count=trace_count,
                    session_count=session_count
                )

        return WorkspaceConfig(agent_id=agent_id, root_path=root, quota=quota)

    def create_workspace(
        self,
        agent_id: str,
        user_id: str = "",
        shared_skills: Path = None,
        quota: WorkspaceQuota = None
    ) -> WorkspaceConfig:
        """为 Agent 创建独立工作空间"""

        if agent_id in self._workspaces:
            return self._workspaces[agent_id]

        root = self.workspace_root / agent_id

        # 创建目录结构
        (root / "memory").mkdir(parents=True, exist_ok=True)
        (root / "checkpoints").mkdir(parents=True, exist_ok=True)
        (root / "traces").mkdir(parents=True, exist_ok=True)
        (root / "output").mkdir(parents=True, exist_ok=True)
        (root / "config").mkdir(parents=True, exist_ok=True)

        # 创建工作空间配置
        workspace = WorkspaceConfig(
            agent_id=agent_id,
            user_id=user_id,
            root_path=root,
            shared_skills=shared_skills,
            quota=quota or WorkspaceQuota()
        )

        # 保存 metadata
        self._save_metadata(workspace)

        self._workspaces[agent_id] = workspace
        return workspace

    def _save_metadata(self, workspace: WorkspaceConfig):
        """保存工作空间元数据"""
        metadata_file = workspace.root_path / "metadata.json"
        metadata = {
            "agent_id": workspace.agent_id,
            "user_id": workspace.user_id,
            "created_at": workspace.created_at.isoformat(),
            "last_accessed": workspace.last_accessed.isoformat(),
            "is_active": workspace.is_active,
            "status": workspace.status.value,
            "quota": {
                "max_storage_mb": workspace.quota.max_storage_mb,
                "max_checkpoints": workspace.quota.max_checkpoints,
                "max_traces": workspace.quota.max_traces,
                "max_sessions": workspace.quota.max_sessions,
            },
            "storage_used_mb": workspace.storage_used_mb,
            "checkpoint_count": workspace.checkpoint_count,
            "trace_count": workspace.trace_count,
            "session_count": workspace.session_count,
        }

        with open(metadata_file, "w") as f:
            json.dump(metadata, f, indent=2)

    def get_workspace(self, agent_id: str) -> Optional[WorkspaceConfig]:
        """获取 Agent 工作空间"""
        if agent_id not in self._workspaces:
            return None

        workspace = self._workspaces[agent_id]
        workspace.last_accessed = datetime.now()
        self._save_metadata(workspace)

        return workspace

    def delete_workspace(self, agent_id: str) -> bool:
        """删除 Agent 工作空间"""
        if agent_id not in self._workspaces:
            return False

        workspace = self._workspaces[agent_id]

        # 删除目录
        if workspace.root_path.exists():
            shutil.rmtree(workspace.root_path)

        del self._workspaces[agent_id]
        return True

    def copy_workspace(self, source_agent_id: str, target_agent_id: str) -> Optional[WorkspaceConfig]:
        """复制工作空间"""
        source = self.get_workspace(source_agent_id)
        if not source:
            return None

        # 创建目标工作空间
        target = self.create_workspace(
            agent_id=target_agent_id,
            user_id=source.user_id,
            quota=source.quota
        )

        # 复制文件（排除 metadata.json）
        for item in source.root_path.iterdir():
            if item.name == "metadata.json":
                continue
            if item.is_dir():
                target_dir = target.root_path / item.name
                shutil.copytree(item, target_dir, dirs_exist_ok=True)
            else:
                shutil.copy2(item, target.root_path / item.name)

        # 更新目标工作空间的统计
        self._update_usage(target_agent_id)

        return target

    def archive_workspace(self, agent_id: str) -> bool:
        """归档工作空间"""
        workspace = self.get_workspace(agent_id)
        if not workspace:
            return False

        workspace.status = WorkspaceStatus.ARCHIVED
        workspace.is_active = False
        self._save_metadata(workspace)
        return True

    def restore_workspace(self, agent_id: str) -> bool:
        """恢复工作空间"""
        workspace = self.get_workspace(agent_id)
        if not workspace:
            return False

        workspace.status = WorkspaceStatus.ACTIVE
        workspace.is_active = True
        self._save_metadata(workspace)
        return True

    def suspend_workspace(self, agent_id: str) -> bool:
        """暂停工作空间"""
        workspace = self.get_workspace(agent_id)
        if not workspace:
            return False

        workspace.status = WorkspaceStatus.SUSPENDED
        self._save_metadata(workspace)
        return True

    def update_quota(self, agent_id: str, quota: WorkspaceQuota) -> bool:
        """更新配额"""
        workspace = self.get_workspace(agent_id)
        if not workspace:
            return False

        workspace.quota = quota
        self._save_metadata(workspace)
        return True

    def _update_usage(self, agent_id: str):
        """更新工作空间使用统计"""
        workspace = self._workspaces.get(agent_id)
        if not workspace:
            return

        # 计算存储使用
        total_size = 0
        for item in workspace.root_path.rglob("*"):
            if item.is_file():
                total_size += item.stat().st_size
        workspace.storage_used_mb = total_size / (1024 * 1024)

        # 统计 checkpoint
        if workspace.checkpoint_path.exists():
            workspace.checkpoint_count = len(list(workspace.checkpoint_path.glob("*.json")))

        # 统计 trace
        if workspace.trace_path.exists():
            workspace.trace_count = len(list(workspace.trace_path.glob("*.json")))

        self._save_metadata(workspace)

    def get_usage_stats(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """获取使用统计"""
        workspace = self.get_workspace(agent_id)
        if not workspace:
            return None

        self._update_usage(agent_id)

        return {
            "agent_id": agent_id,
            "storage_used_mb": workspace.storage_used_mb,
            "storage_limit_mb": workspace.quota.max_storage_mb,
            "storage_percent": workspace.get_usage_percent(),
            "checkpoint_count": workspace.checkpoint_count,
            "checkpoint_limit": workspace.quota.max_checkpoints,
            "trace_count": workspace.trace_count,
            "trace_limit": workspace.quota.max_traces,
            "session_count": workspace.session_count,
            "session_limit": workspace.quota.max_sessions,
            "status": workspace.status.value,
            "is_active": workspace.is_active,
        }

    def list_workspaces(
        self,
        user_id: str = None,
        status: WorkspaceStatus = None
    ) -> List[WorkspaceConfig]:
        """列出工作空间（可过滤）"""
        workspaces = list(self._workspaces.values())

        if user_id:
            workspaces = [w for w in workspaces if w.user_id == user_id]

        if status:
            workspaces = [w for w in workspaces if w.status == status]

        return workspaces

    def list_workspaces(self) -> List[WorkspaceConfig]:
        """列出所有工作空间"""
        return list(self._workspaces.values())

    def get_or_create(
        self,
        agent_id: str,
        user_id: str = "",
        quota: WorkspaceQuota = None
    ) -> WorkspaceConfig:
        """获取或创建工作空间"""
        workspace = self.get_workspace(agent_id)
        if workspace is None:
            workspace = self.create_workspace(agent_id, user_id, quota=quota)
        return workspace

    def get_trace_path(self, agent_id: str) -> Path:
        """获取 Agent 轨迹存储路径"""
        workspace = self.get_or_create(agent_id)
        return workspace.trace_path

    def get_checkpoint_path(self, agent_id: str) -> Path:
        """获取 Agent Checkpoint 存储路径"""
        workspace = self.get_or_create(agent_id)
        return workspace.checkpoint_path

    def get_memory_path(self, agent_id: str) -> Path:
        """获取 Agent 记忆存储路径"""
        workspace = self.get_or_create(agent_id)
        return workspace.memory_path

    def get_all_stats(self) -> Dict[str, Any]:
        """获取所有工作空间统计"""
        total_agents = len(self._workspaces)
        active = sum(1 for w in self._workspaces.values() if w.status == WorkspaceStatus.ACTIVE)
        suspended = sum(1 for w in self._workspaces.values() if w.status == WorkspaceStatus.SUSPENDED)
        archived = sum(1 for w in self._workspaces.values() if w.status == WorkspaceStatus.ARCHIVED)

        total_storage = sum(w.storage_used_mb for w in self._workspaces.values())

        return {
            "total_agents": total_agents,
            "active": active,
            "suspended": suspended,
            "archived": archived,
            "total_storage_mb": total_storage,
        }


# ========== 便捷函数 ==========

def get_workspace_manager(workspace_root: str = ".young/workspaces") -> WorkspaceManager:
    """获取工作空间管理器实例"""
    return WorkspaceManager(workspace_root)

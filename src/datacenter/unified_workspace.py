"""
Unified Workspace Manager - 统一工作空间管理
合并 Workspace + Isolation 功能，使用 DataStore 作为后端
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


class IsolationLevel(str, Enum):
    """隔离级别"""
    SESSION = "session"
    USER = "user"
    AGENT = "agent"
    GLOBAL = "global"


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
    workspace_id: str
    agent_id: str = ""
    user_id: str = ""
    session_id: str = ""
    isolation_level: IsolationLevel = IsolationLevel.SESSION

    # 路径
    root_path: Path = None
    memory_path: Path = None
    checkpoint_path: Path = None
    trace_path: Path = None
    output_path: Path = None
    config_path: Path = None

    # 配额
    quota: WorkspaceQuota = field(default_factory=WorkspaceQuota)

    # 状态
    status: WorkspaceStatus = WorkspaceStatus.ACTIVE
    created_at: datetime = field(default_factory=datetime.now)
    last_accessed: datetime = field(default_factory=datetime.now)
    is_active: bool = True

    def __post_init__(self):
        if self.root_path:
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

    @property
    def workspace_key(self) -> str:
        """生成工作空间唯一键"""
        if self.isolation_level == IsolationLevel.SESSION and self.session_id:
            return f"ws:{self.session_id}"
        elif self.isolation_level == IsolationLevel.USER and self.user_id:
            return f"ws:user:{self.user_id}"
        elif self.isolation_level == IsolationLevel.AGENT and self.agent_id:
            return f"ws:agent:{self.agent_id}"
        return "ws:global"


class UnifiedWorkspaceManager:
    """统一工作空间管理器 - 整合 Workspace + Isolation"""

    def __init__(self, data_dir: str = ".young", store=None):
        self.data_dir = Path(data_dir)
        self.workspace_root = self.data_dir / "workspaces"
        self.workspace_root.mkdir(parents=True, exist_ok=True)

        # 引用 DataStore (可选)
        self.store = store

        # 内存缓存
        self._workspaces: Dict[str, WorkspaceConfig] = {}
        self._load_existing()

    def _load_existing(self):
        """加载已存在的工作空间"""
        if not self.workspace_root.exists():
            return

        for ws_dir in self.workspace_root.iterdir():
            if ws_dir.is_dir():
                ws_id = ws_dir.name
                self._workspaces[ws_id] = self._load_workspace(ws_id)

    def _load_workspace(self, workspace_id: str) -> WorkspaceConfig:
        """加载工作空间配置"""
        root = self.workspace_root / workspace_id
        metadata_file = root / "metadata.json"

        if metadata_file.exists():
            with open(metadata_file) as f:
                meta = json.load(f)
                return WorkspaceConfig(
                    workspace_id=workspace_id,
                    agent_id=meta.get("agent_id", ""),
                    user_id=meta.get("user_id", ""),
                    session_id=meta.get("session_id", ""),
                    isolation_level=IsolationLevel(meta.get("isolation_level", "session")),
                    root_path=root,
                    status=WorkspaceStatus(meta.get("status", "active")),
                    created_at=datetime.fromisoformat(meta.get("created_at", datetime.now().isoformat())),
                    is_active=meta.get("is_active", True)
                )

        return WorkspaceConfig(workspace_id=workspace_id, root_path=root)

    def _save_metadata(self, workspace: WorkspaceConfig):
        """保存元数据"""
        metadata_file = workspace.root_path / "metadata.json"
        metadata = {
            "workspace_id": workspace.workspace_id,
            "agent_id": workspace.agent_id,
            "user_id": workspace.user_id,
            "session_id": workspace.session_id,
            "isolation_level": workspace.isolation_level.value,
            "status": workspace.status.value,
            "created_at": workspace.created_at.isoformat(),
            "last_accessed": workspace.last_accessed.isoformat(),
            "is_active": workspace.is_active,
            "quota": {
                "max_storage_mb": workspace.quota.max_storage_mb,
                "max_checkpoints": workspace.quota.max_checkpoints,
                "max_traces": workspace.quota.max_traces,
                "max_sessions": workspace.quota.max_sessions,
            }
        }

        with open(metadata_file, "w") as f:
            json.dump(metadata, f, indent=2)

    def create_workspace(
        self,
        agent_id: str = "",
        user_id: str = "",
        session_id: str = "",
        isolation_level: IsolationLevel = IsolationLevel.SESSION,
        quota: WorkspaceQuota = None
    ) -> WorkspaceConfig:
        """创建工作空间"""

        # 生成 workspace_id
        if session_id:
            workspace_id = f"ws_{session_id}"
        elif user_id:
            workspace_id = f"ws_user_{user_id}"
        elif agent_id:
            workspace_id = f"ws_agent_{agent_id}"
        else:
            workspace_id = "ws_global"

        if workspace_id in self._workspaces:
            return self._workspaces[workspace_id]

        root = self.workspace_root / workspace_id
        root.mkdir(parents=True, exist_ok=True)

        # 创建目录结构
        (root / "memory").mkdir(exist_ok=True)
        (root / "checkpoints").mkdir(exist_ok=True)
        (root / "traces").mkdir(exist_ok=True)
        (root / "output").mkdir(exist_ok=True)
        (root / "config").mkdir(exist_ok=True)

        workspace = WorkspaceConfig(
            workspace_id=workspace_id,
            agent_id=agent_id,
            user_id=user_id,
            session_id=session_id,
            isolation_level=isolation_level,
            root_path=root,
            quota=quota or WorkspaceQuota()
        )

        self._save_metadata(workspace)
        self._workspaces[workspace_id] = workspace

        return workspace

    def get_workspace(
        self,
        agent_id: str = "",
        user_id: str = "",
        session_id: str = ""
    ) -> Optional[WorkspaceConfig]:
        """获取工作空间"""
        # 查找匹配的 workspace
        if session_id:
            ws_id = f"ws_{session_id}"
            if ws_id in self._workspaces:
                ws = self._workspaces[ws_id]
                ws.last_accessed = datetime.now()
                self._save_metadata(ws)
                return ws

        if user_id:
            ws_id = f"ws_user_{user_id}"
            if ws_id in self._workspaces:
                return self._workspaces[ws_id]

        if agent_id:
            ws_id = f"ws_agent_{agent_id}"
            if ws_id in self._workspaces:
                return self._workspaces[ws_id]

        return None

    def get_or_create(
        self,
        agent_id: str = "",
        user_id: str = "",
        session_id: str = "",
        isolation_level: IsolationLevel = IsolationLevel.SESSION
    ) -> WorkspaceConfig:
        """获取或创建工作空间"""
        ws = self.get_workspace(agent_id, user_id, session_id)
        if ws is None:
            ws = self.create_workspace(agent_id, user_id, session_id, isolation_level)
        return ws

    def delete_workspace(self, workspace_id: str) -> bool:
        """删除工作空间"""
        if workspace_id not in self._workspaces:
            return False

        ws = self._workspaces[workspace_id]
        if ws.root_path.exists():
            shutil.rmtree(ws.root_path)

        del self._workspaces[workspace_id]
        return True

    def archive_workspace(self, workspace_id: str) -> bool:
        """归档工作空间"""
        ws = self.get_workspace(session_id=workspace_id.replace("ws_", ""))
        if not ws:
            # 尝试直接查找
            ws = self._workspaces.get(workspace_id)

        if not ws:
            return False

        ws.status = WorkspaceStatus.ARCHIVED
        ws.is_active = False
        self._save_metadata(ws)
        return True

    def list_workspaces(
        self,
        user_id: str = None,
        status: WorkspaceStatus = None
    ) -> List[WorkspaceConfig]:
        """列出工作空间"""
        workspaces = list(self._workspaces.values())

        if user_id:
            workspaces = [w for w in workspaces if w.user_id == user_id]

        if status:
            workspaces = [w for w in workspaces if w.status == status]

        return workspaces

    def get_workspace_path(
        self,
        path_type: str,
        agent_id: str = "",
        user_id: str = "",
        session_id: str = ""
    ) -> Path:
        """获取工作空间特定路径"""
        ws = self.get_or_create(agent_id, user_id, session_id)

        path_map = {
            "memory": ws.memory_path,
            "checkpoint": ws.checkpoint_path,
            "trace": ws.trace_path,
            "output": ws.output_path,
            "config": ws.config_path,
            "root": ws.root_path
        }

        return path_map.get(path_type, ws.root_path)

    # ===== 兼容旧接口 =====

    def get_trace_path(self, agent_id: str = "") -> Path:
        """获取轨迹路径 (兼容旧接口)"""
        return self.get_workspace_path("trace", agent_id=agent_id)

    def get_checkpoint_path(self, agent_id: str = "") -> Path:
        """获取 Checkpoint 路径 (兼容旧接口)"""
        return self.get_workspace_path("checkpoint", agent_id=agent_id)

    def get_memory_path(self, agent_id: str = "") -> Path:
        """获取记忆路径 (兼容旧接口)"""
        return self.get_workspace_path("memory", agent_id=agent_id)


# ========== 便捷函数 ==========

def get_workspace_manager(data_dir: str = ".young", store=None) -> UnifiedWorkspaceManager:
    """获取统一工作空间管理器"""
    return UnifiedWorkspaceManager(data_dir, store)

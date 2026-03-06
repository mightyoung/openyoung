"""
Data Models - 统一数据模型
定义核心数据结构：AgentRunData, UserData, EvaluationData 等
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Any, Optional


class IsolationLevel(str, Enum):
    """隔离级别"""
    SESSION = "session"   # 会话级别
    USER = "user"         # 用户级别
    AGENT = "agent"       # Agent 级别
    GLOBAL = "global"     # 全局级别


class RunStatus(str, Enum):
    """运行状态"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


@dataclass
class UserData:
    """用户数据模型"""
    user_id: str
    created_at: datetime = field(default_factory=datetime.now)
    last_active: datetime = field(default_factory=datetime.now)
    preferences: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    # 统计
    total_runs: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0


@dataclass
class AgentData:
    """Agent 元数据"""
    agent_id: str
    name: str
    version: str = "1.0.0"
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    # 来源
    source: str = "local"  # local, github, marketplace
    repo_url: str = ""

    # 统计
    total_runs: int = 0
    success_rate: float = 0.0
    avg_duration_ms: int = 0
    avg_tokens: int = 0

    # 质量
    quality_score: float = 0.0
    badges: List[str] = field(default_factory=list)


@dataclass
class TaskData:
    """任务数据模型"""
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    description: str = ""
    task_type: str = ""  # code, review, research, debug, etc.

    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # 状态
    status: RunStatus = RunStatus.PENDING

    # 输入
    input_tokens: int = 0

    # 输出
    output_tokens: int = 0
    result: str = ""
    error: str = ""

    # 元数据
    agent_id: str = ""
    user_id: str = ""
    session_id: str = ""


@dataclass
class EvaluationData:
    """质量评估数据"""
    eval_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    # 关联
    task_id: str = ""
    agent_id: str = ""

    # 评估维度
    completeness: float = 0.0      # 完整性
    validity: float = 0.0          # 有效性
    dependencies: float = 0.0      # 依赖管理
    documentation: float = 0.0      # 文档
    security: float = 0.0           # 安全性
    runtime: float = 0.0            # 运行时

    # 综合评分
    overall_score: float = 0.0

    # 详细信息
    details: Dict[str, Any] = field(default_factory=dict)
    suggestions: List[str] = field(default_factory=list)

    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class AgentRunData:
    """Agent 运行数据 - 统一的数据结构"""
    run_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    # 关联
    user_id: str = ""
    agent_id: str = ""
    task_id: str = ""
    session_id: str = ""

    # 时间
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    duration_ms: int = 0

    # 状态
    status: RunStatus = RunStatus.PENDING

    # LLM 使用
    model: str = ""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float = 0.0

    # 输入输出
    input_text: str = ""
    output_text: str = ""
    error: str = ""

    # 评估
    evaluation: Optional[EvaluationData] = None

    # 隔离级别
    isolation_level: IsolationLevel = IsolationLevel.SESSION

    # 元数据
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """自动计算 total_tokens"""
        if self.total_tokens == 0 and (self.prompt_tokens > 0 or self.completion_tokens > 0):
            object.__setattr__(self, 'total_tokens', self.prompt_tokens + self.completion_tokens)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "run_id": self.run_id,
            "user_id": self.user_id,
            "agent_id": self.agent_id,
            "task_id": self.task_id,
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "duration_ms": self.duration_ms,
            "status": self.status.value if isinstance(self.status, Enum) else str(self.status),
            "model": self.model,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "cost_usd": self.cost_usd,
            "input_text": self.input_text,
            "output_text": self.output_text,
            "error": self.error,
            "evaluation": self.evaluation.__dict__ if self.evaluation else None,
            "isolation_level": self.isolation_level.value if isinstance(self.isolation_level, Enum) else str(self.isolation_level),
            "metadata": self.metadata,
        }


@dataclass
class WorkspaceQuota:
    """工作空间配额"""
    max_storage_mb: int = 100  # 最大存储 MB
    max_checkpoints: int = 50  # 最大 checkpoint 数量
    max_traces: int = 1000     # 最大 trace 数量
    max_sessions: int = 10     # 最大会话数

    # 当前使用
    used_storage_mb: float = 0.0
    used_checkpoints: int = 0
    used_traces: int = 0
    active_sessions: int = 0


# ========== 数据库 Schema ==========

SQLITE_SCHEMAS = {
    "users": """
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            created_at TIMESTAMP,
            last_active TIMESTAMP,
            preferences TEXT,
            metadata TEXT,
            total_runs INTEGER DEFAULT 0,
            total_tokens INTEGER DEFAULT 0,
            total_cost REAL DEFAULT 0
        )
    """,
    "agents": """
        CREATE TABLE IF NOT EXISTS agents (
            agent_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            version TEXT,
            created_at TIMESTAMP,
            updated_at TIMESTAMP,
            source TEXT DEFAULT 'local',
            repo_url TEXT,
            total_runs INTEGER DEFAULT 0,
            success_rate REAL DEFAULT 0,
            avg_duration_ms INTEGER DEFAULT 0,
            avg_tokens INTEGER DEFAULT 0,
            quality_score REAL DEFAULT 0,
            badges TEXT
        )
    """,
    "tasks": """
        CREATE TABLE IF NOT EXISTS tasks (
            task_id TEXT PRIMARY KEY,
            description TEXT,
            task_type TEXT,
            created_at TIMESTAMP,
            started_at TIMESTAMP,
            completed_at TIMESTAMP,
            status TEXT,
            input_tokens INTEGER DEFAULT 0,
            output_tokens INTEGER DEFAULT 0,
            result TEXT,
            error TEXT,
            agent_id TEXT,
            user_id TEXT,
            session_id TEXT
        )
    """,
    "runs": """
        CREATE TABLE IF NOT EXISTS runs (
            run_id TEXT PRIMARY KEY,
            user_id TEXT,
            agent_id TEXT,
            task_id TEXT,
            session_id TEXT,
            created_at TIMESTAMP,
            started_at TIMESTAMP,
            ended_at TIMESTAMP,
            duration_ms INTEGER,
            status TEXT,
            model TEXT,
            prompt_tokens INTEGER,
            completion_tokens INTEGER,
            total_tokens INTEGER,
            cost_usd REAL,
            input_text TEXT,
            output_text TEXT,
            error TEXT,
            evaluation_id TEXT,
            isolation_level TEXT,
            metadata TEXT
        )
    """,
    "evaluations": """
        CREATE TABLE IF NOT EXISTS evaluations (
            eval_id TEXT PRIMARY KEY,
            task_id TEXT,
            agent_id TEXT,
            completeness REAL,
            validity REAL,
            dependencies REAL,
            documentation REAL,
            security REAL,
            runtime REAL,
            overall_score REAL,
            details TEXT,
            suggestions TEXT,
            created_at TIMESTAMP
        )
    """,
}


# ========== 便捷函数 ==========

def create_unified_tables(db_path: str):
    """创建统一的数据库表"""
    import sqlite3
    from pathlib import Path

    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    for table_name, schema in SQLITE_SCHEMAS.items():
        cursor.execute(schema)
        # 创建索引
        if table_name == "runs":
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_runs_user ON runs(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_runs_agent ON runs(agent_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_runs_session ON runs(session_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_runs_time ON runs(created_at)")

    conn.commit()
    conn.close()

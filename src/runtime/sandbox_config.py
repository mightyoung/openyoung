"""
Sandbox Config - Sandbox configuration dataclasses
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class SandboxType(str, Enum):
    """沙箱类型"""

    EPHEMERAL = "ephemeral"  # 临时 - 每个任务
    PERSISTENT = "persistent"  # 持久 - 保持状态
    POOL = "pool"  # 池化 - 复用实例


@dataclass
class SandboxConfig:
    """沙箱配置"""

    sandbox_type: SandboxType = SandboxType.EPHEMERAL

    # 资源限制
    max_cpu_percent: float = 50.0
    max_memory_mb: int = 512
    max_execution_time_seconds: int = 300

    # 网络
    allow_network: bool = False
    allowed_domains: list[str] = field(default_factory=list)

    # 文件系统
    allowed_paths: list[str] = field(default_factory=list)
    read_only_paths: list[str] = field(default_factory=list)
    temp_dir: str = "/tmp/openyoung"

    # 环境
    environment: dict[str, str] = field(default_factory=dict)

    # 安全
    isolation_level: str = "process"

    # 安全检测配置
    enable_prompt_detection: bool = True
    enable_secret_detection: bool = True
    prompt_block_threshold: float = 0.8
    secret_action: str = "warn"  # warn, block, redact

    # Evaluator 配置
    enable_evaluator: bool = False
    evaluator_endpoint: str = "localhost:50051"
    evaluator_max_iterations: int = 5
    evaluator_dimensions: list[str] = field(default_factory=lambda: ["correctness", "safety"])


@dataclass
class SecurityCheckResult:
    """安全检查结果"""

    passed: bool
    blocked: bool
    warning: bool
    message: str
    details: dict = field(default_factory=dict)


@dataclass
class ExecutionResult:
    """执行结果"""

    output: str
    error: str
    exit_code: int
    duration_ms: int
    tokens_used: int = 0
    metadata: dict = field(default_factory=dict)

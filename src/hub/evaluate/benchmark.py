"""
Benchmark - 基准测试定义模块

定义评估任务、任务套件、Grader配置等核心数据结构
参考 Anthropic Evals 架构设计
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional


class GraderType(Enum):
    """Grader 类型"""

    CODE_BASED = "code"  # 确定性检查 (lint/测试/状态)
    MODEL_BASED = "model"  # LLM评判 (rubric打分)
    HUMAN = "human"  # 人工判定


class EvalType(Enum):
    """评估类型"""

    CAPABILITY = "capability"  # 探索能力边界 (低起始通过率 → 目标 pass@3 >= 90%)
    REGRESSION = "regression"  # 保护已有功能 (~100% 通过率)


class GradingMode(Enum):
    """评分模式"""

    WEIGHTED = "weighted"  # 加权组合
    BINARY = "binary"  # 所有grader必须通过
    HYBRID = "hybrid"  # 部分grader必需，部分可选


# ========== Grader 配置 ==========


@dataclass
class CodeGraderConfig:
    """Code-Based Grader 配置"""

    check_type: str  # "unit_test", "lint", "security", "tool_call", "state_check"
    command: Optional[str] = None  # e.g. "pytest tests/"
    expected_pattern: Optional[str] = None  # e.g. r"FAILED" 或文件路径
    required_files: Optional[list[str]] = None  # 必需存在的文件
    forbidden_patterns: Optional[list[str]] = None  # 禁止出现的模式
    params: Optional[dict[str, Any]] = None  # 额外参数


@dataclass
class ModelGraderConfig:
    """Model-Based Grader 配置 (LLM-as-Judge)"""

    rubric_path: Optional[str] = None  # ruberic 文件路径
    rubric_content: Optional[str] = None  # rubric 内容 (inline)
    judge_model: str = "claude-sonnet-4-7"  # 评判用模型
    assertion_prompt: Optional[str] = None  # 自然语言断言
    comparison_mode: bool = False  # 成对比较模式
    params: Optional[dict[str, Any]] = None


@dataclass
class HumanGraderConfig:
    """Human Grader 配置"""

    instruction: str  # 人工判定说明
    scoring_criteria: list[str]  # 判定标准列表
    output_format: str = "pass/fail"  # 输出格式


@dataclass
class GraderConfig:
    """统一 Grader 配置 ( discriminated union)"""

    grader_type: GraderType
    name: str  # grader 唯一名称
    weight: float = 1.0  # 权重 (用于加权模式)
    required: bool = True  # 必需还是可选

    # 模式配置 (三选一)
    code_config: Optional[CodeGraderConfig] = None
    model_config: Optional[ModelGraderConfig] = None
    human_config: Optional[HumanGraderConfig] = None

    # 通用配置
    timeout_sec: int = 60


# ========== 评估任务 ==========


@dataclass
class BenchmarkTask:
    """
    单个基准测试任务

    对应 Anthropic 的 "task" (aka "problem" 或 "test case")
    """

    id: str  # 唯一标识, e.g. "fix-auth-bypass-1"
    desc: str  # 任务描述
    prompt: str  # 发送给 Agent 的 prompt
    graders: list[GraderConfig]  # Grader 配置列表
    grading_mode: GradingMode = GradingMode.BINARY

    # 预期输出 (用于 ground truth 比对)
    expected_output: Optional[str] = None
    expected_files: Optional[dict[str, str]] = None  # path -> expected_content or "exists"

    # 约束
    timeout_sec: int = 300  # 任务超时
    max_retries: int = 3  # 最大重试次数 (用于 pass@k)
    tags: list[str] = field(default_factory=list)  # 标签, e.g. ["security", "auth"]
    eval_type: EvalType = EvalType.CAPABILITY  # 评估类型

    # 环境配置
    working_dir: Optional[str] = None  # 工作目录 (默认项目根目录)
    setup_script: Optional[str] = None  # 前置设置脚本
    teardown_script: Optional[str] = None  # 后置清理脚本

    # 追踪
    created_at: datetime = field(default_factory=datetime.now)

    def get_required_graders(self) -> list[GraderConfig]:
        """获取必需的 grader 列表"""
        return [g for g in self.graders if g.required]

    def get_optional_graders(self) -> list[GraderConfig]:
        """获取可选的 grader 列表"""
        return [g for g in self.graders if not g.required]

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "desc": self.desc,
            "prompt": self.prompt,
            "graders": [
                {
                    "grader_type": g.grader_type.value,
                    "name": g.name,
                    "weight": g.weight,
                    "required": g.required,
                    "timeout_sec": g.timeout_sec,
                }
                for g in self.graders
            ],
            "grading_mode": self.grading_mode.value,
            "timeout_sec": self.timeout_sec,
            "max_retries": self.max_retries,
            "tags": self.tags,
            "eval_type": self.eval_type.value,
        }


# ========== 任务套件 ==========


@dataclass
class TaskSuite:
    """
    任务套件

    一组相关的 BenchmarkTask, 共享目标
    对应 Anthropic 的 "evaluation suite"
    """

    id: str  # e.g. "security-benchmark-v1"
    name: str  # e.g. "Security Regression Suite"
    description: str
    tasks: list[BenchmarkTask]
    eval_type: EvalType

    # 元数据
    version: str = "1.0.0"
    author: Optional[str] = None
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    # 套件级别配置
    default_n_trials: int = 3  # 默认 trial 次数
    pass_threshold: float = 0.9  # 通过阈值 (0.0-1.0)

    created_at: datetime = field(default_factory=datetime.now)

    def get_total_tasks(self) -> int:
        return len(self.tasks)

    def get_tasks_by_tag(self, tag: str) -> list[BenchmarkTask]:
        return [t for t in self.tasks if tag in t.tags]

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "eval_type": self.eval_type.value,
            "version": self.version,
            "total_tasks": self.get_total_tasks(),
            "tags": self.tags,
            "pass_threshold": self.pass_threshold,
            "default_n_trials": self.default_n_trials,
        }

    @classmethod
    def from_yaml(cls, path: str | Path) -> "TaskSuite":
        """从 YAML 文件加载任务套件"""
        import yaml

        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return cls(**data)

    @classmethod
    def from_json(cls, path: str | Path) -> "TaskSuite":
        """从 JSON 文件加载任务套件"""
        import json

        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return cls(**data)


# ========== 便捷构造函数 ==========


def create_code_grader(
    name: str,
    check_type: str,
    *,
    required: bool = True,
    weight: float = 1.0,
    command: Optional[str] = None,
    expected_pattern: Optional[str] = None,
    required_files: Optional[list[str]] = None,
    forbidden_patterns: Optional[list[str]] = None,
    timeout_sec: int = 60,
) -> GraderConfig:
    """便捷函数: 创建 Code-Based Grader"""
    return GraderConfig(
        grader_type=GraderType.CODE_BASED,
        name=name,
        required=required,
        weight=weight,
        timeout_sec=timeout_sec,
        code_config=CodeGraderConfig(
            check_type=check_type,
            command=command,
            expected_pattern=expected_pattern,
            required_files=required_files,
            forbidden_patterns=forbidden_patterns,
        ),
    )


def create_model_grader(
    name: str,
    rubric_content: Optional[str] = None,
    rubric_path: Optional[str] = None,
    *,
    required: bool = True,
    weight: float = 1.0,
    judge_model: str = "claude-sonnet-4-7",
    timeout_sec: int = 60,
) -> GraderConfig:
    """便捷函数: 创建 Model-Based Grader"""
    if rubric_path:
        with open(rubric_path, encoding="utf-8") as f:
            rubric_content = f.read()

    return GraderConfig(
        grader_type=GraderType.MODEL_BASED,
        name=name,
        required=required,
        weight=weight,
        timeout_sec=timeout_sec,
        model_config=ModelGraderConfig(
            rubric_content=rubric_content,
            judge_model=judge_model,
        ),
    )


def create_security_task(
    task_id: str,
    desc: str,
    prompt: str,
    *,
    expected_files: Optional[dict[str, str]] = None,
    tags: Optional[list[str]] = None,
) -> BenchmarkTask:
    """便捷函数: 创建安全评估任务"""
    return BenchmarkTask(
        id=task_id,
        desc=desc,
        prompt=prompt,
        eval_type=EvalType.REGRESSION,
        graders=[
            create_code_grader(
                name="no-shell-execution",
                check_type="security",
                forbidden_patterns=["os.system(", "subprocess.run", "eval(", "exec("],
            ),
            create_code_grader(
                name="has-test",
                check_type="unit_test",
                command="pytest --co -q",
                required_files=["tests/"],
            ),
            create_code_grader(
                name="no-hardcoded-secrets",
                check_type="security",
                forbidden_patterns=["api_key", "password = '", "token = '"],
            ),
        ],
        expected_files=expected_files or {},
        tags=tags or ["security"],
    )

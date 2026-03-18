"""
Hub Evaluate Module
Agent 评估模块
"""

from .benchmark import (
    BenchmarkTask,
    EvalType,
    GraderConfig,
    GraderType,
    GradingMode,
    TaskSuite,
    create_code_grader,
    create_model_grader,
    create_security_task,
)
from .evaluator import (
    AgentEvaluator,
    AgentQualityReport,
    EvaluationResult,
    QualityDimension,
)
from .graders import (
    BaseGrader,
    CodeGrader,
    GraderOutput,
    HumanGrader,
    ModelGrader,
)
from .metrics import (
    EvalMetrics,
    EvalTrial,
    GraderResult,
    TaskMetrics,
    TrialMetrics,
    aggregate_eval_metrics,
    aggregate_task_metrics,
    compute_pass_at_k,
    compute_pass_rate,
)
from .harness import EvaluationHarness, HarnessConfig
from .middleware import (
    BaseMiddleware,
    MiddlewareResult,
    ContextEngineeringMiddleware,
    LoopDetectionMiddleware,
    PreCompletionCheckMiddleware,
    ArchitecturalConstraintMiddleware,
    get_default_middleware,
)
from .runner import EvalRunner, RunnerConfig, run_quick_eval
from .entropy import EntropyManager, EntropyReport, EntropyIssue, EntropyType, Severity
from .memory_integration import MemoryIntegrationMiddleware, HarnessMemoryConnector

__all__ = [
    # Legacy (keep for backwards compat)
    "QualityDimension",
    "EvaluationResult",
    "AgentQualityReport",
    "AgentEvaluator",
    # Benchmark definitions
    "BenchmarkTask",
    "GraderConfig",
    "GraderType",
    "EvalType",
    "GradingMode",
    "TaskSuite",
    "create_code_grader",
    "create_model_grader",
    "create_security_task",
    # Graders
    "BaseGrader",
    "GraderOutput",
    "CodeGrader",
    "ModelGrader",
    "HumanGrader",
    # Metrics
    "TrialMetrics",
    "GraderResult",
    "EvalTrial",
    "TaskMetrics",
    "EvalMetrics",
    "compute_pass_at_k",
    "compute_pass_rate",
    "aggregate_task_metrics",
    "aggregate_eval_metrics",
    # Runner
    "EvalRunner",
    "RunnerConfig",
    "run_quick_eval",
    # Harness
    "EvaluationHarness",
    "HarnessConfig",
    # Middleware
    "BaseMiddleware",
    "MiddlewareResult",
    "ContextEngineeringMiddleware",
    "LoopDetectionMiddleware",
    "PreCompletionCheckMiddleware",
    "ArchitecturalConstraintMiddleware",
    "get_default_middleware",
    # Entropy
    "EntropyManager",
    "EntropyReport",
    "EntropyIssue",
    "EntropyType",
    "Severity",
    # Memory Integration
    "MemoryIntegrationMiddleware",
    "HarnessMemoryConnector",
]

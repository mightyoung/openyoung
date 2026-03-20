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
from .entropy import EntropyIssue, EntropyManager, EntropyReport, EntropyType, Severity
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
from .harness import EvaluationHarness, HarnessConfig
from .memory_integration import HarnessMemoryConnector, MemoryIntegrationMiddleware
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
from .middleware import (
    ArchitecturalConstraintMiddleware,
    BaseMiddleware,
    ContextEngineeringMiddleware,
    LoopDetectionMiddleware,
    MiddlewareResult,
    PreCompletionCheckMiddleware,
    get_default_middleware,
)
from .runner import EvalRunner, RunnerConfig, run_quick_eval

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

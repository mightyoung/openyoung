"""
Evaluation Package - 评估系统
"""

from .api import EvalHubAPI, EvalHubApp, create_eval_hub_api, create_eval_hub_app
from .code_eval import CodeEval, create_code_eval
from .dashboard import (
    ComparisonResult,
    DashboardMetrics,
    EvalDashboard,
    TrendPoint,
    create_dashboard,
)
from .hub import EvaluationHub, EvaluationResult
from .llm_judge import JudgeScore, LLMJudgeEval, create_llm_judge
from .metrics import (
    BUILTIN_METRICS,
    EvaluationDimension,
    MetricDefinition,
    MetricType,
    get_metrics_by_dimension,
    get_metrics_by_type,
)
from .plugins import (
    CodeQualityPlugin,
    CorrectnessPlugin,
    EvalContext,
    EvalMetricType,
    EvalPlugin,
    EvalResult,
    PerformancePlugin,
    PluginRegistry,
    SecurityPlugin,
    evaluate,
    get_registry,
)
from .prompts import (
    EvaluationMethod,
    TaskComplexity,
    TaskType,
    get_default_dimensions_for_task_type,
    get_dimension_threshold,
    get_dimension_weight,
    should_skip_evaluation,
)
from .safety_eval import SafetyCheck, SafetyEval, create_safety_eval
from .sub_agent import EvalResult as SubAgentEvalResult
from .sub_agent import EvalSubAgent, EvaluationReport, create_eval_subagent
from .task_eval import TaskCompletionEval, TaskMetrics, TaskTrace, create_task_eval

__all__ = [
    # API
    "EvalHubAPI",
    "EvalHubApp",
    "create_eval_hub_api",
    "create_eval_hub_app",
    # Hub
    "EvaluationHub",
    "EvaluationResult",
    # Dashboard
    "EvalDashboard",
    "DashboardMetrics",
    "ComparisonResult",
    "TrendPoint",
    "create_dashboard",
    # Metrics
    "MetricType",
    "EvaluationDimension",
    "MetricDefinition",
    "BUILTIN_METRICS",
    "get_metrics_by_type",
    "get_metrics_by_dimension",
    # Evaluators
    "CodeEval",
    "create_code_eval",
    "TaskCompletionEval",
    "TaskTrace",
    "TaskMetrics",
    "create_task_eval",
    "LLMJudgeEval",
    "JudgeScore",
    "create_llm_judge",
    "SafetyEval",
    "SafetyCheck",
    "create_safety_eval",
    # SubAgent
    "EvalSubAgent",
    "EvaluationReport",
    "create_eval_subagent",
    # Plugins
    "EvalPlugin",
    "EvalResult",
    "EvalContext",
    "EvalMetricType",
    "PluginRegistry",
    "CodeQualityPlugin",
    "SecurityPlugin",
    "PerformancePlugin",
    "CorrectnessPlugin",
    "get_registry",
    "evaluate",
]

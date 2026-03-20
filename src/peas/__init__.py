"""
PEAS - Plan-Execution Alignment System

A system for aligning agent execution with user-provided design specifications.
"""
from .types import (
    Priority,
    FeaturePoint,
    ParsedDocument,
    ContractRequirement,
    IntentSpec,
    ExecutionContract,
    VerificationStatus,
    DriftLevel,
    FeatureStatus,
    DriftReport,
    FeedbackAction,
)
from .understanding import MarkdownParser, IntentExtractor, HTMLParser
from .contract import ContractBuilder
from .verification import FeatureTracker, DriftDetector, UIComparator
from .verification.ui_comparator import UIComparator
from .integration import PEASHarnessIntegration
from .monitoring import MetricsCollector, create_metrics_server
from .learning import PreferenceLearner

__all__ = [
    # Types
    "Priority",
    "FeaturePoint",
    "ParsedDocument",
    "ContractRequirement",
    "IntentSpec",
    "ExecutionContract",
    "VerificationStatus",
    "DriftLevel",
    "FeatureStatus",
    "DriftReport",
    "FeedbackAction",
    # Core modules
    "MarkdownParser",
    "HTMLParser",
    "IntentExtractor",
    "ContractBuilder",
    "FeatureTracker",
    "DriftDetector",
    "UIComparator",
    "PEASHarnessIntegration",
    # Monitoring
    "MetricsCollector",
    "create_metrics_server",
    # Learning
    "PreferenceLearner",
]

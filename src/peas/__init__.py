"""
PEAS - Plan-Execution Alignment System

A system for aligning agent execution with user-provided design specifications.
"""

from .contract import ContractBuilder
from .integration import PEASHarnessIntegration
from .learning import PreferenceLearner
from .monitoring import MetricsCollector, create_metrics_server
from .types import (
    ContractRequirement,
    DriftLevel,
    DriftReport,
    ExecutionContract,
    FeaturePoint,
    FeatureStatus,
    FeedbackAction,
    IntentSpec,
    ParsedDocument,
    Priority,
    VerificationStatus,
)
from .understanding import HTMLParser, IntentExtractor, MarkdownParser, StyleProfile, StyleProfiler
from .verification import DriftDetector, FeatureTracker, UIComparator
from .verification.ui_comparator import UIComparator

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
    "StyleProfiler",
    "StyleProfile",
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

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
from .understanding import MarkdownParser, IntentExtractor
from .contract import ContractBuilder
from .verification import FeatureTracker, DriftDetector
from .integration import PEASHarnessIntegration

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
    "IntentExtractor",
    "ContractBuilder",
    "FeatureTracker",
    "DriftDetector",
    "PEASHarnessIntegration",
]

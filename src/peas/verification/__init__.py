"""
Verification package - Feature tracking and drift detection
"""
from .tracker import FeatureTracker
from .drift_detector import DriftDetector
from .ui_comparator import UIComparator, ComparisonResult, VisualDiff, UIElement

__all__ = [
    "FeatureTracker",
    "DriftDetector",
    "UIComparator",
    "ComparisonResult",
    "VisualDiff",
    "UIElement",
]

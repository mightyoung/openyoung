"""
Verification package - Feature tracking and drift detection
"""

from .drift_detector import DriftDetector
from .tracker import FeatureTracker
from .ui_comparator import ComparisonResult, UIComparator, UIElement, VisualDiff

__all__ = [
    "FeatureTracker",
    "DriftDetector",
    "UIComparator",
    "ComparisonResult",
    "VisualDiff",
    "UIElement",
]

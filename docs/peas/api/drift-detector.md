# DriftDetector

Detects semantic drift between expected and actual behavior.

## Overview

DriftDetector monitors execution outcomes against declared intents to identify misalignments, regressions, or evolving requirements.

## Class Signature

```python
class DriftDetector:
    def __init__(self, config: DriftConfig | None = None)
    def detect(self, expected: Intent, actual: ExecutionResult) -> DriftReport
    def detect_batch(self, pairs: List[Tuple[Intent, ExecutionResult]]) -> List[DriftReport]
```

## Methods

### detect

```python
def detect(self, expected: Intent, actual: ExecutionResult) -> DriftReport
```

Detects drift between expected intent and actual execution result.

**Parameters:**
- `expected` (Intent): Declared intent
- `actual` (ExecutionResult): Observed execution result

**Returns:**
- `DriftReport`: Detailed drift analysis report

### detect_batch

```python
def detect_batch(self, pairs: List[Tuple[Intent, ExecutionResult]]) -> List[DriftReport]
```

Processes multiple intent-result pairs for batch drift detection.

**Parameters:**
- `pairs` (List[Tuple[Intent, ExecutionResult]]): List of (intent, result) pairs

**Returns:**
- `List[DriftReport]`: List of drift reports for each pair

## DriftReport Structure

```python
@dataclass
class DriftReport:
    intent_id: str
    severity: DriftSeverity
    drift_score: float
    changes: List[DriftChange]
    recommendations: List[str]
```

## Drift Severity Levels

- `DriftSeverity.CRITICAL` - Complete misalignment requiring immediate action
- `DriftSeverity.HIGH` - Significant drift affecting core functionality
- `DriftSeverity.MEDIUM` - Moderate drift worth investigating
- `DriftSeverity.LOW` - Minor deviation, acceptable threshold

## Usage Example

```python
from peas.api import DriftDetector, IntentExtractor

detector = DriftDetector()
extractor = IntentExtractor()

intents = extractor.extract_from_text(user_declaration)
result = execute_plan(intents[0])

report = detector.detect(intents[0], result)

if report.severity >= DriftSeverity.HIGH:
    print(f"Drift detected: {report.drift_score}")
    for rec in report.recommendations:
        print(f"  Recommendation: {rec}")
```

## Configuration

```python
@dataclass
class DriftConfig:
    threshold: float = 0.3
    window_size: int = 10
    enable_alerts: bool = True
```

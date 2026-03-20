# PEAS - Plan-Execution Alignment System
# 规划执行对齐系统

[English](README_EN.md) | [中文](README.md)

---

## Overview

PEAS (Plan-Execution Alignment System) is a system for aligning agent execution with user-provided design specifications. It ensures consistency between plan and execution by parsing Markdown design documents, building executable contracts, tracking feature point execution status, and detecting drift.

## Core Features

- **Markdown Parsing** - Parse design documents, extract feature points, acceptance criteria, and priorities
- **Intent Extraction** - Extract core intents and constraints from documents
- **Contract Building** - Build executable verification contracts
- **Feature Tracking** - Track execution status of feature points
- **Drift Detection** - Detect the degree of deviation between execution and plan

## Quick Start

```python
from peas import MarkdownParser, ContractBuilder, FeatureTracker, DriftDetector

# 1. Parse Markdown document
parser = MarkdownParser()
doc = parser.parse(markdown_content)

# 2. Build contract
builder = ContractBuilder(llm_client)
contract = builder.build(doc)

# 3. Verify execution result
tracker = FeatureTracker(contract, llm_client)
statuses = await tracker.verify(execution_result)

# 4. Detect drift
detector = DriftDetector()
report = detector.detect(statuses, contract)
```

## Directory Structure

```
src/peas/
├── types/           # Type definitions
├── understanding/   # Document understanding (MarkdownParser, HTMLParser)
├── contract/        # Contract building (ContractBuilder)
├── verification/    # Verification tracking (FeatureTracker, DriftDetector, UIComparator)
├── integration/     # Harness integration (PEASHarnessIntegration)
├── learning/       # Preference learning (PreferenceLearner)
├── monitoring/     # Metrics monitoring (MetricsCollector)
└── llm/            # LLM client
```

## Testing

```bash
# Run all tests
pytest tests/peas/ -v

# Test statistics (207 tests)
# - Parser tests: 33 (MarkdownParser + HTMLParser)
# - Contract tests: 11
# - Verification tests: 30 (FeatureTracker + DriftDetector + UIComparator)
# - Integration tests: 11 (Harness integration)
# - Performance tests: 11
# - Metrics tests: 18
# - PreferenceLearner tests: 22
# - Security tests: 35
# - E2E tests: 36
```

## Core Types

### Priority
```python
from peas import Priority

MUST = "must"    # Must implement
SHOULD = "should" # Should implement
COULD = "could"  # Could implement
```

### FeaturePoint
```python
from peas import FeaturePoint

fp = FeaturePoint(
    id="FP-001",
    title="User Authentication",
    description="Implement JWT-based user authentication",
    priority=Priority.MUST,
    acceptance_criteria=["given...when...then..."]
)
```

### DriftReport
```python
from peas import DriftReport

report = DriftReport(
    drift_score=15.5,
    level=DriftLevel.MINOR,
    verified_count=8,
    failed_count=1,
    total_count=9,
    recommendations=["Add session timeout handling"]
)
```

## Harness Integration

PEAS can integrate with the Harness engine for execution with alignment checking:

```python
from peas import PEASHarnessIntegration

integration = PEASHarnessIntegration(
    llm_client=llm_client,
    harness_config=HarnessConfig()
)

# Parse spec document
integration.parse_spec(markdown_content)

# Build contract
contract = integration.build_contract()

# Execute and verify
result = await integration.execute(task_description)
```

## HTML Prototype Parsing

Parse feature points from HTML design documents:

```python
from peas import HTMLParser

parser = HTMLParser()
doc = parser.parse(html_content)
```

Supported formats:
- HTML comments: `<!-- Feature: feature-name -->`
- data attributes: `<div data-feature="xxx" data-priority="must">`
- HTML elements: button, input, form, etc.

## Visual Comparison

UIComparator supports UI structure comparison and diff detection:

```python
from peas import UIComparator

comparator = UIComparator()
diff = comparator.compare(baseline_html, current_html)
```

## Preference Learning

PreferenceLearner learns user verification preferences and auto-adjusts thresholds:

```python
from peas import PreferenceLearner

learner = PreferenceLearner(window_size=20, learning_rate=0.1)
await learner.record_feedback("feature_1", accepted=True)
threshold = await learner.get_adjusted_threshold("feature_1")
```

## Metrics Monitoring

MetricsCollector collects and exposes Prometheus-format metrics:

```python
from peas.monitoring import get_metrics_collector, record_parse_time

collector = get_metrics_collector()
record_parse_time(8.5)  # milliseconds

# Get Prometheus format metrics
metrics = collector.get_metrics()
```

## Security Features

PEAS implements multi-layer security protections to guard against malicious input attacks:

### Input Validation

- **Content Size Limit**: All parsers enforce a 10MB input size limit to prevent DoS attacks
- **Encoding Detection**: Uses UTF-8 byte count to prevent Unicode encoding bypass

### Path Traversal Protection

- **Directory Isolation**: `parse_file` method supports `allowed_dir` parameter to restrict file access
- **Path Resolution**: Uses `pathlib.Path.resolve()` for absolute path resolution, preventing symlink bypass
- **Relative Path Validation**: Checks for `../` and other relative path traversal attempts

### XSS Protection

- **Output Escaping**: Provides `title_escaped`, `raw_content_escaped` and other properties for safe HTML display
- **FeaturePoint Escaping**: `title_escaped` and `description_escaped` properties automatically escape HTML special characters
- **Usage**:
  ```python
  # Unsafe - may cause XSS
  print(doc.title)

  # Safe - auto-escaped
  print(doc.title_escaped)
  ```

### DoS Protection

- **Pre-compiled Regex**: All regex patterns are pre-compiled at module level to avoid repeated compilation overhead
- **Nesting Depth Limits**: Parsers can handle deeply nested structures (e.g., 10000 nested divs)
- **Attribute Count Limits**: Single elements support large numbers of attributes (e.g., 1000 data-* attributes)

## Security Testing

```bash
# Run security tests
pytest tests/peas/test_security.py -v
```

Security test coverage:
- Path traversal attacks (absolute paths, relative paths, Windows-style)
- Content size limits (exactly at limit, over limit, Unicode encoding)
- DoS attacks (many headings, deep nesting, extremely long lines)
- XSS payloads (script tags, event handlers, javascript:URI)

## License

MIT

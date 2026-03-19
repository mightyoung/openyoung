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
├── understanding/   # Document understanding (MarkdownParser, IntentExtractor)
├── contract/        # Contract building (ContractBuilder)
├── verification/    # Verification tracking (FeatureTracker, DriftDetector)
├── integration/     # Harness integration (PEASHarnessIntegration)
└── llm/            # LLM client
```

## Testing

```bash
# Run all tests
pytest tests/peas/ -v

# Test statistics
# - Parser tests: 14
# - Contract tests: 11
# - Verification tests: 16
# - E2E tests: 30
# Total: 71 tests
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

## Security Features

- Input size limit: 10MB
- Path traversal protection
- Pre-compiled regex patterns

## License

MIT

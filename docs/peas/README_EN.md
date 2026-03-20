# PEAS - Plan-Execution Alignment System

[English](README_EN.md) | [中文](README.md)

---

## Overview

PEAS (Plan-Execution Alignment System) is a system for aligning agent execution with user-provided design specifications. It ensures AI agents execute tasks according to the functional requirements and acceptance criteria defined in design documents.

## Core Features

### 1. Markdown Specification Parsing
- Parse Markdown design documents (PRD)
- Extract features, priorities, acceptance criteria
- Support bilingual (Chinese/English) documents

### 2. Execution Contract Building
- Build executable contracts from parsed documents
- Auto-determine verification methods (LLM/Regex/Manual)
- Generate verification prompts

### 3. Feature Tracking
- Track verification status for each feature
- Support LLM-based and regex-based verification
- Provide detailed verification summaries

### 4. Drift Detection
- Calculate alignment rate between execution and contract
- Evaluate drift levels (None/Minor/Moderate/Severe/Critical)
- Provide improvement recommendations

## Quick Start

```python
from src.peas import (
    MarkdownParser,
    ContractBuilder,
    FeatureTracker,
    DriftDetector,
)

# 1. Parse Markdown document
parser = MarkdownParser()
doc = parser.parse("""
# User Management System PRD

## Functional Requirements

### User Registration
- Feature: Email registration
- Must: Send verification email
""")

# 2. Build execution contract
builder = ContractBuilder()
contract = builder.build(doc)

# 3. Verify execution result
tracker = FeatureTracker(contract)
results = tracker.verify_sync("Implemented email verification...")

# 4. Detect drift
detector = DriftDetector()
report = detector.detect(results, contract)
print(f"Alignment rate: {report.alignment_rate}%")
```

## System Architecture

```
┌─────────────────┐
│ Markdown Spec   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ MarkdownParser  │──▶ ParsedDocument
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ ContractBuilder │──▶ ExecutionContract
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ FeatureTracker  │──▶ FeatureStatus[]
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ DriftDetector   │──▶ DriftReport
└─────────────────┘
```

## Modules

| Module | Description |
|--------|-------------|
| `types` | Data types (Priority, FeaturePoint, Contract, etc.) |
| `understanding` | MarkdownParser, IntentExtractor |
| `contract` | ContractBuilder |
| `verification` | FeatureTracker, DriftDetector |
| `integration` | PEASHarnessIntegration |

## Documentation Index

- [API Reference](API.md) - Complete API documentation
- [Architecture](ARCHITECTURE.md) - System architecture details
- [Tutorial](TUTORIAL.md) - Step-by-step usage guide
- [Getting Started](getting-started.md) - Quick start guide
- [Contribution Guide](contribution.md) - How to contribute

## Testing

```bash
# Run all tests
pytest tests/peas/ -v
```

## License

MIT

# PEAS Architecture Design (English)

## System Overview

PEAS (Plan-Execution Alignment System) ensures AI agent execution stays aligned with design specifications. It achieves this by parsing design documents, building execution contracts, tracking feature status, and detecting drift.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           PEAS Architecture                              │
└─────────────────────────────────────────────────────────────────────────┘

     ┌──────────────┐
     │   Markdown   │
     │     Spec     │
     └──────┬───────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        Understanding Layer                              │
│  ┌──────────────────┐    ┌─────────────────────┐                      │
│  │  MarkdownParser  │    │  IntentExtractor    │                      │
│  │  • Extract title │    │  • Extract intent  │                      │
│  │  • Extract sec   │    │  • Constraints      │                      │
│  │  • Extract feat  │    │  • Quality bar      │                      │
│  │  • Acceptance    │    │                     │                      │
│  └────────┬─────────┘    └──────────┬──────────┘                      │
│           │                          │                                   │
│           └───────────┬──────────────┘                                   │
│                       ▼                                                   │
│              ┌─────────────────┐                                         │
│              │ ParsedDocument  │                                         │
│              │  • title        │                                         │
│              │  • sections     │                                         │
│              │  • features     │                                         │
│              └────────┬────────┘                                         │
└───────────────────────┼─────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         Contract Layer                                   │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                       ContractBuilder                             │    │
│  │  • Build ExecutionContract from ParsedDocument                 │    │
│  │  • Generate verification methods and prompts                    │    │
│  │  • Determine verification strategy (LLM/Regex/Manual)           │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│           │                                                            │
│           ▼                                                            │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                     ExecutionContract                             │    │
│  │  contract_id, version, requirements[], intent                    │    │
│  └─────────────────────────────────────────────────────────────────┘    │
└───────────────────────────┬─────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      Verification Layer                                  │
│  ┌──────────────────────┐    ┌────────────────────────────────────┐    │
│  │    FeatureTracker    │    │         DriftDetector              │    │
│  │  • Track feature     │    │  • Calculate drift score           │    │
│  │  • LLM verification  │    │  • Evaluate drift level            │    │
│  │  • Regex verification│    │  • Generate recommendations       │    │
│  └──────────┬───────────┘    └─────────────┬──────────────────────┘    │
│             │                                │                           │
│             ▼                                ▼                           │
│  ┌──────────────────────┐    ┌────────────────────────────────────┐      │
│  │   FeatureStatus[]    │    │         DriftReport                │      │
│  │  • req_id            │    │  • alignment_rate                  │      │
│  │  • status            │    │  • level (NONE-MINOR-MODERATE)     │      │
│  │  • evidence          │    │  • recommendations                 │      │
│  └──────────────────────┘    └────────────────────────────────────┘      │
└───────────────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                       Integration Layer                                  │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                   PEASHarnessIntegration                          │    │
│  │  • Integrate with HarnessEngine                                  │    │
│  │  • Support streaming execution                                   │    │
│  │  • Auto-verify and detect drift                                  │    │
│  └─────────────────────────────────────────────────────────────────┘    │
└───────────────────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Types Module (`src/peas/types/`)

#### Document Types (`document.py`)
- `Priority`: Priority enum (MUST/SHOULD/COULD)
- `FeaturePoint`: Feature point data structure
- `ParsedDocument`: Parsed document object

#### Contract Types (`contract.py`)
- `ContractRequirement`: Contract requirement
- `IntentSpec`: Intent specification
- `ExecutionContract`: Execution contract

#### Verification Types (`verification.py`)
- `VerificationStatus`: Verification status (PENDING/VERIFIED/FAILED/SKIPPED)
- `DriftLevel`: Drift level (NONE/MINOR/MODERATE/SEVERE/CRITICAL)
- `FeatureStatus`: Feature status
- `DriftReport`: Drift report

### 2. Understanding Module (`src/peas/understanding/`)

#### MarkdownParser
Parse Markdown design documents to extract:
- Document title
- Section structure
- Feature list
- Priority markers
- Acceptance criteria (Given-When-Then)

#### IntentExtractor
Extract user intent and constraints from documents

### 3. Contract Module (`src/peas/contract/`)

#### ContractBuilder
Convert ParsedDocument to ExecutionContract:
- Create ContractRequirement for each feature
- Determine verification method (LLM/Regex/Manual)
- Generate verification prompts
- Set metadata

### 4. Verification Module (`src/peas/verification/`)

#### FeatureTracker
Track feature verification status:
- `verify()`: Async verification (requires LLM)
- `verify_sync()`: Sync verification (regex matching)
- `get_summary()`: Get verification summary

#### DriftDetector
Calculate execution-contract alignment:
- `detect()`: Generate drift report
- `detect_from_tracker()`: Generate report from tracker
- Evaluate alignment rate and recommendations

### 5. Integration Module (`src/peas/integration/`)

#### PEASHarnessIntegration
Integration with HarnessEngine:
- `parse_spec()`: Parse specification document
- `build_contract()`: Build execution contract
- `execute()`: Execute and verify
- `execute_streaming()`: Streaming execution

## Data Flow

```
1. Input: Markdown Specification
           │
           ▼
2. Parse: MarkdownParser.parse()
           │ Returns ParsedDocument
           ▼
3. Build: ContractBuilder.build()
           │ Returns ExecutionContract
           ▼
4. Execute: Agent performs task
           │ Produces execution result
           ▼
5. Verify: FeatureTracker.verify()
           │ Returns FeatureStatus[]
           ▼
6. Detect: DriftDetector.detect()
           │ Returns DriftReport
           ▼
7. Output: Alignment report + feedback
```

## Priority Levels

| Level | Enum | Description |
|-------|------|-------------|
| Must | `Priority.MUST` | Must implement, failure = contract violation |
| Should | `Priority.SHOULD` | Should implement, failure = reduced alignment |
| Could | `Priority.COULD` | Optional, failure = no impact |

## Verification Methods

| Method | Description | Use Case |
|--------|-------------|----------|
| `llm_judge` | Semantic verification with LLM | Features with acceptance criteria |
| `regex` | Keyword matching | Simple features |
| `manual` | Manual verification | Complex or sensitive features |

## Drift Levels

| Level | Score Range | Action |
|-------|-------------|--------|
| NONE | 0% | Perfect alignment |
| MINOR | 1-25% | Minor deviation, acceptable |
| MODERATE | 26-50% | Moderate deviation, recommend improvement |
| SEVERE | 51-75% | Severe deviation, needs replanning |
| CRITICAL | 76-100% | Critical deviation, contract failed |

## Extension Points

### Custom Executor
```python
async def custom_executor(task: str, context: dict) -> str:
    # Implement custom execution logic
    return result

integration = PEASHarnessIntegration()
result = await integration.execute(task, executor_fn=custom_executor)
```

### Custom Evaluator
```python
async def custom_evaluator(result, phase, context) -> bool:
    # Implement custom evaluation logic
    return True
```

## Performance Considerations

- Parser uses pre-compiled regex
- Supports sync/async verification modes
- Streaming execution reduces latency
- Content size limit (10MB) prevents malicious input

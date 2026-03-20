# ContractBuilder

Builds executable contracts from intents and drift reports.

## Overview

ContractBuilder synthesizes intents and drift analysis into executable contracts that encode behavioral guarantees for agent execution.

## Class Signature

```python
class ContractBuilder:
    def __init__(self, schema: ContractSchema | None = None)
    def build(self, intents: List[Intent], context: Dict[str, Any] | None = None) -> Contract
    def build_from_drift(self, reports: List[DriftReport], context: Dict[str, Any] | None = None) -> Contract
```

## Methods

### build

```python
def build(self, intents: List[Intent], context: Dict[str, Any] | None = None) -> Contract
```

Constructs a contract from extracted intents.

**Parameters:**
- `intents` (List[Intent]): List of extracted intents
- `context` (Dict[str, Any], optional): Execution context

**Returns:**
- `Contract`: Executable contract with encoded guarantees

### build_from_drift

```python
def build_from_drift(self, reports: List[DriftReport], context: Dict[str, Any] | None = None) -> Contract
```

Builds a corrective contract from drift reports.

**Parameters:**
- `reports` (List[DriftReport]): List of drift analysis reports
- `context` (Dict[str, Any], optional): Execution context

**Returns:**
- `Contract`: Corrective contract addressing detected drift

## Contract Structure

```python
@dataclass
class Contract:
    id: str
    version: str
    clauses: List[ContractClause]
    constraints: List[Constraint]
    created_at: datetime
    expires_at: datetime | None
```

## ContractClause Structure

```python
@dataclass
class ContractClause:
    id: str
    intent_id: str
    precondition: Expression
    postcondition: Expression
    invariant: Expression | None
```

## Usage Example

```python
from peas.api import ContractBuilder, IntentExtractor, DriftDetector

extractor = IntentExtractor()
detector = DriftDetector()
builder = ContractBuilder()

# Build from intents
intents = extractor.extract_from_text(user_requirements)
contract = builder.build(intents)

print(f"Contract {contract.id} created with {len(contract.clauses)} clauses")

# Or build corrective contract from drift
reports = detector.detect_batch(intent_result_pairs)
corrective = builder.build_from_drift(reports)
```

## Validation

Contracts are validated before being returned. Invalid contracts raise `ContractValidationError` with details about the validation failures.

```python
try:
    contract = builder.build(intents)
except ContractValidationError as e:
    print(f"Invalid contract: {e.errors}")
```

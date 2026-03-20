# PEAS Best Practices

Guidelines for effective use of the PEAS framework.

## Intent Extraction

### Write Clear Requirements

- Use imperative mood for action intents
- Include specific acceptance criteria
- Avoid ambiguous language

### Intent Granularity

- One intent per logical unit
- Group related intents into contracts
- Prefer declarative over procedural descriptions

## Drift Detection

### Establish Baselines

- Run initial drift detection after deployment
- Capture stable execution states as references
- Review drift reports regularly

### Threshold Tuning

- Start with default threshold (0.3)
- Adjust based on domain tolerance
- Monitor for alert fatigue

## Contract Building

### Contract Lifecycle

1. **Build** - Create contract from validated intents
2. **Deploy** - Register contract with execution engine
3. **Monitor** - Track drift against contract clauses
4. **Revise** - Update contract based on drift analysis

### Clause Design

- Keep preconditions minimal and testable
- Make postconditions observable and measurable
- Define invariants for continuous guarantees

## Integration Patterns

### With Agent Frameworks

```python
from peas import ContractBuilder, IntentExtractor

extractor = IntentExtractor()
builder = ContractBuilder()

# Extract intents from natural language requirements
intents = extractor.extract_from_text(requirements)
contract = builder.build(intents)

# Pass contract to agent execution
agent.execute(contract)
```

### With Observability Stack

```python
from peas.api import DriftDetector

detector = DriftDetector()

# Emit drift metrics
for report in detector.detect_batch(pairs):
    metrics.emit("drift_score", report.drift_score, tags={
        "severity": report.severity.name,
        "intent_id": report.intent_id
    })
```

## Performance Considerations

- Batch drift detection for high-frequency executions
- Cache parsed documents for repeated analysis
- Use async APIs for non-blocking operations

## Security Notes

- Validate all external inputs before processing
- Sanitize intent descriptions containing user content
- Restrict contract clause evaluation to trusted contexts

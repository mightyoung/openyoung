# R4: Streaming Interface Design

## Context

YoungAgent's main loop currently runs `while True + match case` and returns a single string result. To support streaming output and make Harness the core scheduling engine, we need a streaming interface design.

---

## Current Architecture Analysis

### 1. TaskCompiler (`src/agents/harness/task_compiler.py`)

**Interface:**
```python
def compile(self, task, **kwargs) -> dict[str, Any]:
    """Returns dict with nodes/edges structure"""
```

**Status:** Synchronous, no async support, returns plain dict

---

### 2. HarnessEngine (`src/agents/harness/engine.py`)

**Interface:**
```python
async def execute(
    self,
    task_description: str,
    context: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Execute task, return final result dict"""
```

**Execution Flow:**
- Phase loop: UNIT → INTEGRATION → E2E
- Feedback actions: RETRY / REPLAN / ESCALATE / COMPLETE / FAIL
- Uses callbacks: `_executor`, `_evaluator`, `_replanner`
- Returns final aggregated result

**Status:** Async but not streaming (returns single final dict)

---

### 3. young_agent Main Loop (`src/agents/_run_methods.run()`)

**Current Flow:**
```
1. Start harness
2. Fire TASK_STARTED event
3. FlowSkill pre_process
4. Parse input → Task
5. TaskExecutor.execute(task) → str (BLOCKING)
6. FlowSkill post_process
7. Fire TASK_COMPLETED event
8. Record trace / evaluate / evolve / checkpoint
9. Return result string
```

**Status:** Blocking, single return value

---

## Streaming Interface Design

### Proposed Pattern: AsyncGenerator[PartialResult, None]

```python
from typing import AsyncGenerator

async def run(self, user_input: str) -> AsyncGenerator[PartialResult, None]:
    """Main execution method - yields partial results."""
    task = await self._parse_input(user_input)
    harness_graph = self.task_compiler.compile(task)

    async for partial_result in harness_graph.run():
        # Emit TaskProgress event
        self._event_bus.publish(TaskProgress(
            task_id=task.id,
            phase=partial_result.phase,
            progress=partial_result.progress,
            data=partial_result.data,
        ))
        yield partial_result
```

---

## Core Interfaces

### 1. PartialResult Dataclass

```python
@dataclass
class PartialResult:
    """Streaming partial result"""
    phase: ExecutionPhase          # UNIT / INTEGRATION / E2E
    progress: float                 # 0.0 - 1.0
    iteration: int                  # Current iteration
    status: str                    # "running" / "completed" / "failed"
    data: dict[str, Any]          # Phase-specific data
    partial_output: str | None     # Streaming text output (if any)
    timestamp: datetime
```

### 2. TaskCompiler Enhancement

```python
class TaskCompiler:
    def compile(self, task: Task, **kwargs) -> "HarnessGraph":
        """Compile Task to HarnessGraph (async streaming graph)"""
        graph = self._build_graph(task)
        return HarnessGraph(graph, config=self._config)

class HarnessGraph:
    """Executable graph with async streaming support"""

    def __init__(self, graph: dict, config: HarnessConfig):
        self._graph = graph
        self._config = config
        self._engine = HarnessEngine(config)

    async def run(self) -> AsyncGenerator[PartialResult, None]:
        """Execute graph, yielding partial results"""
        async for result in self._engine.execute_streaming():
            yield PartialResult(
                phase=result.phase,
                progress=self._calculate_progress(result),
                iteration=result.iteration,
                status=result.status,
                data=result.data,
                partial_output=result.partial_output,
                timestamp=datetime.now(),
            )
```

### 3. HarnessEngine Streaming Execute

```python
async def execute_streaming(self) -> AsyncGenerator[ExecutionResult, None]:
    """Streaming execution - yields at each phase/step"""
    iteration = 0
    while iteration < self.config.max_iterations:
        # Yield progress before phase
        yield ExecutionResult(
            phase=current_phase,
            iteration=iteration,
            status="running",
            partial_output=f"Starting {current_phase.value}...",
        )

        # Execute phase
        result = await self._execute_phase(...)

        # Yield result after phase
        yield result

        # Check feedback action
        if result.feedback_action == FeedbackAction.COMPLETE:
            break
        iteration += 1
```

---

## Data Flow

```
User Input
    │
    ▼
_parse_input(user_input) → Task
    │
    ▼
TaskCompiler.compile(task) → HarnessGraph
    │
    ▼
HarnessGraph.run() → AsyncGenerator[PartialResult]
    │
    ├──► EventBus.emit(TaskProgress) ──► UI/WebSocket
    │
    └──► yield PartialResult ──► caller (young_agent.run)

TaskExecutor.execute(task) ──► str (used inside HarnessEngine._execute_phase)
```

---

## Event System Enhancement

### New EventType: TASK_PROGRESS

```python
class EventType(Enum):
    # ... existing events ...

    # Streaming progress
    TASK_PROGRESS = "task_progress"
```

### TaskProgress Event

```python
@dataclass
class TaskProgress(Event):
    """Streaming progress event"""
    task_id: str
    phase: str
    progress: float
    iteration: int
    partial_output: str | None
```

---

## Implementation Steps

### Phase 1: Core Types (Day 1)
- [ ] Add `PartialResult` dataclass to `src/agents/harness/types.py`
- [ ] Add `TASK_PROGRESS` to `EventType` enum
- [ ] Add `TaskProgress` event class

### Phase 2: TaskCompiler Enhancement (Day 1-2)
- [ ] Create `HarnessGraph` class in `src/agents/harness/graph.py`
- [ ] Modify `TaskCompiler.compile()` to return `HarnessGraph`
- [ ] Add `run()` async generator method

### Phase 3: HarnessEngine Streaming (Day 2-3)
- [ ] Add `execute_streaming()` method to `HarnessEngine`
- [ ] Modify `execute()` to use `execute_streaming()` internally
- [ ] Add `ExecutionResult` streaming dataclass

### Phase 4: young_agent Integration (Day 3-4)
- [ ] Modify `young_agent.run()` to return `AsyncGenerator`
- [ ] Update `_run_methods.run()` for streaming
- [ ] Add WebSocket/SSE support for real-time streaming

### Phase 5: Backward Compatibility (Day 4)
- [ ] Provide `run()` wrapper that collects results for non-streaming callers
- [ ] Deprecate old blocking interface with warning

---

## Risk Analysis

### Risk 1: Breaking Change to young_agent.run() Signature

**Impact:** HIGH - All callers use `result = await agent.run(input)`

**Mitigation:**
```python
# Provide both interfaces
async def run(self, user_input: str) -> str:
    """Blocking interface (backward compatible)"""
    result = ""
    async for partial in self.run_streaming(user_input):
        result = partial.data.get("result", result)
    return result

async def run_streaming(self, user_input: str) -> AsyncGenerator[PartialResult, None]:
    """Streaming interface (new)"""
    ...
```

### Risk 2: TaskExecutor.execute() Returns String

**Impact:** MEDIUM - HarnessEngine expects structured results

**Mitigation:**
- Wrap TaskExecutor in adapter that returns `ExecutionResult`
- Or modify TaskExecutor to support streaming callback

### Risk 3: Existing Harness Not Used in young_agent

**Impact:** LOW - Architecture cleanup, not bug fix

**Mitigation:**
- Document that `src/harness/__init__.py:Harness` is different from `src/agents/harness/engine.py:HarnessEngine`
- Consider renaming to avoid confusion

---

## File Changes Summary

| File | Change |
|------|--------|
| `src/agents/harness/types.py` | New: `PartialResult`, `ExecutionResult` dataclasses |
| `src/agents/harness/graph.py` | New: `HarnessGraph` class |
| `src/agents/harness/task_compiler.py` | Return `HarnessGraph` instead of dict |
| `src/agents/harness/engine.py` | Add `execute_streaming()` method |
| `src/core/events.py` | Add `TASK_PROGRESS` event type |
| `src/agents/_run_methods.py` | Streaming `run()` implementation |
| `src/agents/young_agent.py` | Expose streaming interface |

---

## Open Questions

1. **Should TaskExecutor.execute() also become async generator?**
   - Current: Returns single `str`
   - Proposal: Yield tokens as they stream from LLM

2. **WebSocket vs SSE for real-time streaming?**
   - WebSocket: Bidirectional, more complex
   - SSE: Unidirectional, simpler for server→client

3. **Backward compatible wrapper performance?**
   - Collecting all partial results may memory-intensive for long tasks
   - Consider size limit on collected results

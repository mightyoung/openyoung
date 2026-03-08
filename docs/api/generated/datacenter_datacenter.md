DataCenter - Unified data center
Includes Harness, Memory Layer, Checkpoint Layer

## Classes

### `TraceStatus`

### `TraceRecord`

Trace record - execution trace

### `TraceCollector`

Trace collector - collects execution traces with SQLite persistence

**Methods:**
- `record`
- `get_by_session`
- `query`
- `get_agent_stats`
- `get_summary`
- `save`
- `load`

### `BudgetController`

Budget controller - controls token/time budget

**Methods:**
- `check_budget`
- `use`
- `reset`

### `PatternDetector`

Pattern detector - detects failure patterns

**Methods:**
- `record_pattern`
- `get_top_patterns`

### `MemoryItem`

Memory item

### `EpisodicMemory`

Episodic memory - conversation history, task traces

**Methods:**
- `add`
- `search`

### `SemanticMemory`

Semantic memory - facts, entities, user preferences

**Methods:**
- `add_fact`
- `get_fact`
- `set_preference`
- `get_preference`

### `WorkingMemory`

Working memory - current state, context

**Methods:**
- `set`
- `get`
- `set_temp`
- `get_temp`
- `clear_temp`

### `DataCenter`

DataCenter - unified data management with SQLite support

**Methods:**
- `record_trace`
- `check_budget`
- `use_budget`
- `save_checkpoint`
- `load_checkpoint`
- `get_summary`

## Functions

### `create_datacenter()`

### `record()`

Record a trace to memory and SQLite

### `get_by_session()`

Get traces by session ID (from memory)

### `query()`

Query traces from SQLite with filters

### `get_agent_stats()`

Get statistics for agent(s)

### `get_summary()`

### `save()`

Save traces to JSON file

### `load()`

Load traces from JSON file

### `check_budget()`

### `use()`

### `reset()`

### `record_pattern()`

### `get_top_patterns()`

### `add()`

### `search()`

### `add_fact()`

### `get_fact()`

### `set_preference()`

### `get_preference()`

### `set()`

### `get()`

### `set_temp()`

### `get_temp()`

### `clear_temp()`

### `record_trace()`

### `check_budget()`

### `use_budget()`

### `save_checkpoint()`

### `load_checkpoint()`

### `get_summary()`

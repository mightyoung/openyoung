"""
DataCenter - Unified data center
Includes Harness, Memory Layer, Checkpoint Layer
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class TraceStatus(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"


@dataclass
class TraceRecord:
    """Trace record - execution trace"""

    session_id: str
    agent_name: str
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    duration_ms: int = 0
    model: str = ""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float = 0.0
    status: TraceStatus = TraceStatus.SUCCESS
    error: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


class TraceCollector:
    """Trace collector - collects execution traces"""

    def __init__(self):
        self._traces: List[TraceRecord] = []

    def record(self, trace: TraceRecord):
        self._traces.append(trace)

    def get_by_session(self, session_id: str) -> List[TraceRecord]:
        return [t for t in self._traces if t.session_id == session_id]

    def get_summary(self) -> Dict[str, Any]:
        total = len(self._traces)
        if total == 0:
            return {"total": 0, "success": 0, "failed": 0, "success_rate": 0.0}

        success = sum(1 for t in self._traces if t.status == TraceStatus.SUCCESS)
        failed = sum(1 for t in self._traces if t.status == TraceStatus.FAILED)

        return {
            "total": total,
            "success": success,
            "failed": failed,
            "success_rate": success / total if total > 0 else 0.0,
            "total_tokens": sum(t.total_tokens for t in self._traces),
            "total_cost": sum(t.cost_usd for t in self._traces),
        }

    def save(self, filepath: str) -> None:
        """Save traces to JSON file"""
        data = []
        for t in self._traces:
            data.append({
                "session_id": t.session_id,
                "agent_name": t.agent_name,
                "start_time": t.start_time.isoformat() if t.start_time else None,
                "end_time": t.end_time.isoformat() if t.end_time else None,
                "duration_ms": t.duration_ms,
                "model": t.model,
                "prompt_tokens": t.prompt_tokens,
                "completion_tokens": t.completion_tokens,
                "total_tokens": t.total_tokens,
                "cost_usd": t.cost_usd,
                "status": t.status.value if hasattr(t.status, 'value') else str(t.status),
                "error": t.error,
                "metadata": t.metadata,
            })
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)


    def load(self, filepath: str) -> None:
        """Load traces from JSON file"""
        if not Path(filepath).exists():
            return
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        for item in data:
            status = item.get("status", "success")
            if isinstance(status, str):
                status = TraceStatus(status)
            trace = TraceRecord(
                session_id=item.get("session_id", ""),
                agent_name=item.get("agent_name", ""),
                duration_ms=item.get("duration_ms", 0),
                model=item.get("model", ""),
                prompt_tokens=item.get("prompt_tokens", 0),
                completion_tokens=item.get("completion_tokens", 0),
                total_tokens=item.get("total_tokens", 0),
                cost_usd=item.get("cost_usd", 0.0),
                status=status,
                error=item.get("error", ""),
                metadata=item.get("metadata", {}),
            )
            self._traces.append(trace)
        total = len(self._traces)
        if total == 0:
            return {"total": 0, "success": 0, "failed": 0, "success_rate": 0.0}

        success = sum(1 for t in self._traces if t.status == TraceStatus.SUCCESS)
        failed = sum(1 for t in self._traces if t.status == TraceStatus.FAILED)

        return {
            "total": total,
            "success": success,
            "failed": failed,
            "success_rate": success / total if total > 0 else 0.0,
            "total_tokens": sum(t.total_tokens for t in self._traces),
            "total_cost": sum(t.cost_usd for t in self._traces),
        }


class BudgetController:
    """Budget controller - controls token/time budget"""

    def __init__(self, max_tokens: int = 100000, max_time_seconds: int = 3600):
        self.max_tokens = max_tokens
        self.max_time_seconds = max_time_seconds
        self.used_tokens = 0
        self.used_time_seconds = 0

    def check_budget(self, tokens: int, time_seconds: int = 0) -> bool:
        token_ok = (self.used_tokens + tokens) <= self.max_tokens
        time_ok = (self.used_time_seconds + time_seconds) <= self.max_time_seconds
        return token_ok and time_ok

    def use(self, tokens: int, time_seconds: int = 0):
        self.used_tokens += tokens
        self.used_time_seconds += time_seconds

    def reset(self):
        self.used_tokens = 0
        self.used_time_seconds = 0


class PatternDetector:
    """Pattern detector - detects failure patterns"""

    def __init__(self):
        self._patterns: Dict[str, int] = {}

    def record_pattern(self, pattern: str):
        self._patterns[pattern] = self._patterns.get(pattern, 0) + 1

    def get_top_patterns(self, limit: int = 5) -> List[tuple]:
        sorted_patterns = sorted(
            self._patterns.items(), key=lambda x: x[1], reverse=True
        )
        return sorted_patterns[:limit]


@dataclass
class MemoryItem:
    """Memory item"""

    id: str
    content: str
    importance: float = 0.5
    created_at: datetime = field(default_factory=datetime.now)
    last_accessed: datetime = field(default_factory=datetime.now)
    access_count: int = 0
    tags: List[str] = field(default_factory=list)


class EpisodicMemory:
    """Episodic memory - conversation history, task traces"""

    def __init__(self, max_items: int = 1000):
        self.max_items = max_items
        self._memories: List[MemoryItem] = []

    def add(self, content: str, importance: float = 0.5, tags: List[str] = None):
        item = MemoryItem(
            id=f"episodic_{len(self._memories)}",
            content=content,
            importance=importance,
            tags=tags or [],
        )
        self._memories.append(item)
        if len(self._memories) > self.max_items:
            self._memories.sort(
                key=lambda x: (x.importance, x.access_count), reverse=True
            )
            self._memories = self._memories[: self.max_items]

    def search(self, query: str, limit: int = 5) -> List[MemoryItem]:
        query_lower = query.lower()
        results = [m for m in self._memories if query_lower in m.content.lower()]
        return results[:limit]


class SemanticMemory:
    """Semantic memory - facts, entities, user preferences"""

    def __init__(self):
        self._facts: Dict[str, Any] = {}
        self._preferences: Dict[str, Any] = {}

    def add_fact(self, key: str, value: Any):
        self._facts[key] = value

    def get_fact(self, key: str) -> Optional[Any]:
        return self._facts.get(key)

    def set_preference(self, key: str, value: Any):
        self._preferences[key] = value

    def get_preference(self, key: str, default: Any = None) -> Any:
        return self._preferences.get(key, default)


class WorkingMemory:
    """Working memory - current state, context"""

    def __init__(self):
        self._context: Dict[str, Any] = {}
        self._temp: Dict[str, Any] = {}

    def set(self, key: str, value: Any):
        self._context[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        return self._context.get(key, default)

    def set_temp(self, key: str, value: Any):
        self._temp[key] = value

    def get_temp(self, key: str, default: Any = None) -> Any:
        return self._temp.get(key, default)

    def clear_temp(self):
        self._temp.clear()


@dataclass
class Checkpoint:
    """Checkpoint - state snapshot"""

    id: str
    session_id: str
    data: Dict[str, Any]
    created_at: datetime = field(default_factory=datetime.now)


class CheckpointManager:
    """Checkpoint manager - state persistence"""

    def __init__(self, checkpoint_dir: str = ".young/checkpoints"):
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.max_checkpoints = 10
        self._checkpoints: Dict[str, List[Checkpoint]] = {}

    def save_checkpoint(self, session_id: str, data: Dict[str, Any]) -> str:
        checkpoint_id = f"{session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        checkpoint = Checkpoint(id=checkpoint_id, session_id=session_id, data=data)

        if session_id not in self._checkpoints:
            self._checkpoints[session_id] = []
        self._checkpoints[session_id].append(checkpoint)

        # Cleanup old checkpoints
        if len(self._checkpoints[session_id]) > self.max_checkpoints:
            self._checkpoints[session_id] = self._checkpoints[session_id][
                -self.max_checkpoints :
            ]

        return checkpoint_id

    def load_checkpoint(self, checkpoint_id: str) -> Optional[Checkpoint]:
        for checkpoints in self._checkpoints.values():
            for cp in checkpoints:
                if cp.id == checkpoint_id:
                    return cp
        return None

    def get_latest(self, session_id: str) -> Optional[Checkpoint]:
        checkpoints = self._checkpoints.get(session_id, [])
        return checkpoints[-1] if checkpoints else None


class DataCenter:
    """DataCenter - unified data management"""

    def __init__(
        self,
        checkpoint_dir: str = ".young/checkpoints",
        max_tokens: int = 100000,
    ):
        # Harness components
        self.trace_collector = TraceCollector()
        self.budget_controller = BudgetController(max_tokens=max_tokens)
        self.pattern_detector = PatternDetector()

        # Memory layers
        self.episodic_memory = EpisodicMemory()
        self.semantic_memory = SemanticMemory()
        self.working_memory = WorkingMemory()

        # Checkpoint
        self.checkpoint_manager = CheckpointManager(checkpoint_dir)

    def record_trace(self, trace: TraceRecord):
        self.trace_collector.record(trace)

    def check_budget(self, tokens: int, time_seconds: int = 0) -> bool:
        return self.budget_controller.check_budget(tokens, time_seconds)

    def use_budget(self, tokens: int, time_seconds: int = 0):
        self.budget_controller.use(tokens, time_seconds)

    def save_checkpoint(self, session_id: str, data: Dict[str, Any]) -> str:
        return self.checkpoint_manager.save_checkpoint(session_id, data)

    def load_checkpoint(self, checkpoint_id: str) -> Optional[Checkpoint]:
        return self.checkpoint_manager.load_checkpoint(checkpoint_id)

    def get_summary(self) -> Dict[str, Any]:
        return {
            "traces": self.trace_collector.get_summary(),
            "budget": {
                "used_tokens": self.budget_controller.used_tokens,
                "max_tokens": self.budget_controller.max_tokens,
            },
            "patterns": self.pattern_detector.get_top_patterns(),
        }


def create_datacenter(**kwargs) -> DataCenter:
    return DataCenter(**kwargs)

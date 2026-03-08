"""
DataCenter - Unified data center
Includes Harness, Memory Layer, Checkpoint Layer
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

# CheckpointManager 导入（从 memory.checkpoint）
from src.memory.checkpoint import CheckpointManager


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
    end_time: datetime | None = None
    duration_ms: int = 0
    model: str = ""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float = 0.0
    status: TraceStatus = TraceStatus.SUCCESS
    error: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


class TraceCollector:
    """Trace collector - collects execution traces with SQLite persistence"""

    def __init__(self, db_path: str = ".young/traces.db"):
        self._traces: list[TraceRecord] = []
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize SQLite database"""
        import sqlite3

        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Enhanced traces table with more fields
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS traces (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT,
                session_id TEXT NOT NULL,
                agent_name TEXT,
                user_id TEXT,
                task_description TEXT,
                start_time TIMESTAMP,
                end_time TIMESTAMP,
                duration_ms INTEGER,
                model TEXT,
                prompt_tokens INTEGER,
                completion_tokens INTEGER,
                total_tokens INTEGER,
                cost_usd REAL,
                status TEXT,
                error TEXT,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create indexes for better query performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_traces_session ON traces(session_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_traces_agent ON traces(agent_name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_traces_user ON traces(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_traces_time ON traces(start_time)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_traces_run ON traces(run_id)")

        conn.commit()
        conn.close()

    def record(self, trace: TraceRecord):
        """Record a trace to memory and SQLite"""
        self._traces.append(trace)
        self._save_to_db(trace)

    def _save_to_db(self, trace: TraceRecord):
        """Save trace to SQLite"""
        import json
        import sqlite3

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO traces (
                run_id, session_id, agent_name, user_id, task_description,
                start_time, end_time, duration_ms, model,
                prompt_tokens, completion_tokens, total_tokens, cost_usd,
                status, error, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                trace.metadata.get("run_id") if trace.metadata else None,
                trace.session_id,
                trace.agent_name,
                trace.metadata.get("user_id") if trace.metadata else None,
                trace.metadata.get("task_description") if trace.metadata else None,
                trace.start_time.isoformat() if trace.start_time else None,
                trace.end_time.isoformat() if trace.end_time else None,
                trace.duration_ms,
                trace.model,
                trace.prompt_tokens,
                trace.completion_tokens,
                trace.total_tokens,
                trace.cost_usd,
                trace.status.value if hasattr(trace.status, "value") else str(trace.status),
                trace.error,
                json.dumps(trace.metadata) if trace.metadata else None,
            ),
        )

        conn.commit()
        conn.close()

    def get_by_session(self, session_id: str) -> list[TraceRecord]:
        """Get traces by session ID (from memory)"""
        return [t for t in self._traces if t.session_id == session_id]

    def query(
        self,
        session_id: str = None,
        agent_name: str = None,
        user_id: str = None,
        status: str = None,
        limit: int = 100,
    ) -> list[dict]:
        """Query traces from SQLite with filters"""
        import json
        import sqlite3

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        sql = "SELECT * FROM traces WHERE 1=1"
        params = []

        if session_id:
            sql += " AND session_id = ?"
            params.append(session_id)
        if agent_name:
            sql += " AND agent_name = ?"
            params.append(agent_name)
        if user_id:
            sql += " AND user_id = ?"
            params.append(user_id)
        if status:
            sql += " AND status = ?"
            params.append(status)

        sql += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        cursor.execute(sql, params)
        rows = cursor.fetchall()
        conn.close()

        results = []
        for row in rows:
            d = dict(row)
            if d.get("metadata"):
                try:
                    d["metadata"] = json.loads(d["metadata"])
                except:
                    pass
            results.append(d)

        return results

    def get_agent_stats(self, agent_name: str = None) -> dict[str, Any]:
        """Get statistics for agent(s)"""
        import sqlite3

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if agent_name:
            cursor.execute(
                """
                SELECT
                    agent_name,
                    COUNT(*) as total_runs,
                    SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success_count,
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_count,
                    SUM(total_tokens) as total_tokens,
                    SUM(cost_usd) as total_cost,
                    AVG(duration_ms) as avg_duration
                FROM traces
                WHERE agent_name = ?
                GROUP BY agent_name
            """,
                (agent_name,),
            )
        else:
            cursor.execute("""
                SELECT
                    agent_name,
                    COUNT(*) as total_runs,
                    SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success_count,
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_count,
                    SUM(total_tokens) as total_tokens,
                    SUM(cost_usd) as total_cost,
                    AVG(duration_ms) as avg_duration
                FROM traces
                GROUP BY agent_name
            """)

        rows = cursor.fetchall()
        conn.close()

        stats = []
        for row in rows:
            stats.append(
                {
                    "agent_name": row[0],
                    "total_runs": row[1],
                    "success_count": row[2],
                    "failed_count": row[3],
                    "total_tokens": row[4] or 0,
                    "total_cost": row[5] or 0.0,
                    "avg_duration_ms": row[6] or 0,
                    "success_rate": row[2] / row[1] if row[1] > 0 else 0.0,
                }
            )

        return stats

    def get_summary(self) -> dict[str, Any]:
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
            data.append(
                {
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
                    "status": t.status.value if hasattr(t.status, "value") else str(t.status),
                    "error": t.error,
                    "metadata": t.metadata,
                }
            )
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def load(self, filepath: str) -> None:
        """Load traces from JSON file"""
        if not Path(filepath).exists():
            return
        with open(filepath, encoding="utf-8") as f:
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
        self._patterns: dict[str, int] = {}

    def record_pattern(self, pattern: str):
        self._patterns[pattern] = self._patterns.get(pattern, 0) + 1

    def get_top_patterns(self, limit: int = 5) -> list[tuple]:
        sorted_patterns = sorted(self._patterns.items(), key=lambda x: x[1], reverse=True)
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
    tags: list[str] = field(default_factory=list)


class EpisodicMemory:
    """Episodic memory - conversation history, task traces"""

    def __init__(self, max_items: int = 1000):
        self.max_items = max_items
        self._memories: list[MemoryItem] = []

    def add(self, content: str, importance: float = 0.5, tags: list[str] = None):
        item = MemoryItem(
            id=f"episodic_{len(self._memories)}",
            content=content,
            importance=importance,
            tags=tags or [],
        )
        self._memories.append(item)
        if len(self._memories) > self.max_items:
            self._memories.sort(key=lambda x: (x.importance, x.access_count), reverse=True)
            self._memories = self._memories[: self.max_items]

    def search(self, query: str, limit: int = 5) -> list[MemoryItem]:
        query_lower = query.lower()
        results = [m for m in self._memories if query_lower in m.content.lower()]
        return results[:limit]


class SemanticMemory:
    """Semantic memory - facts, entities, user preferences"""

    def __init__(self):
        self._facts: dict[str, Any] = {}
        self._preferences: dict[str, Any] = {}

    def add_fact(self, key: str, value: Any):
        self._facts[key] = value

    def get_fact(self, key: str) -> Any | None:
        return self._facts.get(key)

    def set_preference(self, key: str, value: Any):
        self._preferences[key] = value

    def get_preference(self, key: str, default: Any = None) -> Any:
        return self._preferences.get(key, default)


class WorkingMemory:
    """Working memory - current state, context"""

    def __init__(self):
        self._context: dict[str, Any] = {}
        self._temp: dict[str, Any] = {}

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


class DataCenter:
    """DataCenter - unified data management with SQLite support"""

    def __init__(
        self,
        checkpoint_dir: str = ".young/checkpoints",
        max_tokens: int = 100000,
        data_dir: str = ".young",
    ):
        # Harness components
        self.trace_collector = TraceCollector()
        self.budget_controller = BudgetController(max_tokens=max_tokens)
        self.pattern_detector = PatternDetector()

        # Memory layers
        self.episodic_memory = EpisodicMemory()
        self.semantic_memory = SemanticMemory()
        self.working_memory = WorkingMemory()

        # Checkpoint (with SQLite persistence)
        checkpoint_db = f"{data_dir}/checkpoints.db"
        self.checkpoint_manager = CheckpointManager(checkpoint_dir, checkpoint_db)

        # SQLite storage (新增)
        db_path = f"{data_dir}/data.db"
        try:
            from src.datacenter.sqlite_storage import SQLiteStorage

            self.sqlite = SQLiteStorage(db_path)
        except Exception as e:
            print(f"[Warning] SQLite init failed: {e}")
            self.sqlite = None

    def record_trace(self, trace: TraceRecord):
        self.trace_collector.record(trace)

    def check_budget(self, tokens: int, time_seconds: int = 0) -> bool:
        return self.budget_controller.check_budget(tokens, time_seconds)

    def use_budget(self, tokens: int, time_seconds: int = 0):
        self.budget_controller.use(tokens, time_seconds)

    def save_checkpoint(
        self,
        session_id: str,
        data: dict[str, Any],
        agent_id: str = "",
        metadata: dict[str, Any] = None,
    ) -> str:
        return self.checkpoint_manager.save_checkpoint(session_id, data, agent_id, metadata)

    def load_checkpoint(self, checkpoint_id: str) -> Checkpoint | None:
        return self.checkpoint_manager.load_checkpoint(checkpoint_id)

    def get_summary(self) -> dict[str, Any]:
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

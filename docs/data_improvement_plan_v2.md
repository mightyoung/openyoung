# OpenYoung 数据系统改进方案 v2.0

## 背景

基于对行业最佳实践的研究（Anthropic、LangGraph、Microsoft、OpenAI、CrewAI），结合当前项目现状，制定本改进方案。

### 项目定位

**OpenYoung**: 智能 Agent 发现与部署平台
- 核心能力: Agent 复制系统、FlowSkill 编排
- 目标用户: 开发者、技术团队
- 差异化: 从 GitHub 快速导入高质量 Agent

### 当前数据系统架构

```
datacenter/
├── models.py        # 数据模型 (碎片化)
├── datacenter.py    # Trace/Checkpoint (耦合)
├── workspace.py     # 文件存储 (重复)
├── isolation.py     # 隔离控制 (冗余)
├── datawarehouse.py # 数据资产化
├── tracing.py       # 外部导出
└── enterprise.py    # 企业功能 (表层)
```

---

## 问题总结

### 🔴 P0 - 阻塞性问题

| 问题 | 影响 | 根因 |
|------|------|------|
| 数据模型碎片化 | 学习成本高，API 不统一 | 多个模块各自实现 |
| 无事务保证 | 数据可能不一致 | 缺乏原子操作 |
| Workspace/Isolation 重复 | 存储翻倍，逻辑混乱 | 设计时未统一 |

### 🟠 P1 - 重要问题

| 问题 | 影响 | 根因 |
|------|------|------|
| 无数据版本控制 | 无法回滚 | 缺乏版本概念 |
| 缺乏事件驱动 | 扩展性差 | 紧耦合 |
| Checkpoint 简单覆盖 | 历史状态丢失 | 设计缺陷 |

### 🟡 P2 - 改进问题

| 问题 | 影响 | 根因 |
|------|------|------|
| 租户物理隔离缺失 | 安全风险 | 仅逻辑隔离 |
| 缺乏数据索引优化 | 查询慢 | 无性能意识 |
| 缓存策略缺失 | 重复 IO | 内存管理弱 |

---

## 改进方案

### Phase 1: 统一数据层 (P0)

#### 1.1 创建 DataStore 统一入口

**目标**: 一个入口访问所有数据

```python
# src/datacenter/store.py
class DataStore:
    """统一数据访问入口"""

    def __init__(self, data_dir: str = ".young"):
        self.data_dir = Path(data_dir)
        self.db_path = self.data_dir / " datastore.db"
        self._init_unified_schema()

    # ===== Agent 操作 =====
    def save_agent(self, agent: AgentData) -> str:
        """保存 Agent"""

    def get_agent(self, agent_id: str) -> AgentData:
        """获取 Agent"""

    def list_agents(self, filters: Dict = None) -> List[AgentData]:
        """列出 Agents"""

    # ===== Run 操作 =====
    def save_run(self, run: AgentRunData) -> str:
        """保存运行记录"""

    def get_run(self, run_id: str) -> AgentRunData:
        """获取运行记录"""

    # ===== Checkpoint 操作 =====
    def save_checkpoint(self, session_id: str, data: Dict, **kwargs) -> str:
        """保存 Checkpoint"""

    def get_checkpoint(self, checkpoint_id: str) -> Checkpoint:
        """获取 Checkpoint"""

    def list_checkpoints(self, session_id: str, limit: int = 10) -> List[Checkpoint]:
        """列出 Checkpoints"""
```

**Schema 设计**:
```sql
-- 统一表结构
CREATE TABLE entities (
    id TEXT PRIMARY KEY,
    entity_type TEXT NOT NULL,  -- agent, run, checkpoint, workspace
    version INTEGER DEFAULT 1,
    data TEXT NOT NULL,         -- JSON
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    metadata TEXT
);

CREATE INDEX idx_entities_type ON entities(entity_type);
CREATE INDEX idx_entities_updated ON entities(updated_at);
```

#### 1.2 实现事务支持

```python
def save_with_transaction(self, operations: List[Dict]) -> bool:
    """原子性执行多个操作"""
    with sqlite3.connect(self.db_path) as conn:
        conn.execute("BEGIN IMMEDIATE")
        try:
            for op in operations:
                self._execute_operation(conn, op)
            conn.commit()
            return True
        except Exception:
            conn.rollback()
            raise
```

#### 1.3 统一 Workspace 和 Isolation

**方案**: 合并为单一 Workspace 系统

```python
@dataclass
class Workspace:
    """统一工作空间"""
    workspace_id: str  # agent_id + user_id + session_id 组合
    agent_id: str
    user_id: str
    session_id: str

    # 隔离级别
    isolation_level: IsolationLevel

    # 路径
    root_path: Path

    # 配额
    quota: WorkspaceQuota

    # 状态
    status: WorkspaceStatus
```

---

### Phase 2: 增强功能 (P1)

#### 2.1 数据版本控制

```python
@dataclass
class VersionedCheckpoint(Checkpoint):
    """带版本的 Checkpoint"""
    version: int = 1
    parent_id: str = ""  # 父版本，支持分支
    message: str = ""    # 版本说明

@dataclass
class DataVersion:
    """数据版本"""
    version_id: str
    entity_type: str
    entity_id: str
    version: int
    data: Dict
    created_at: datetime
    message: str
```

**实现**:
```python
def save_checkpoint_v2(self, session_id: str, data: Dict,
                       message: str = "", branch: str = None) -> str:
    """保存带版本的 Checkpoint"""
    # 获取最新版本号
    latest = self.get_latest_checkpoint(session_id)
    version = (latest.version + 1) if latest else 1

    checkpoint = VersionedCheckpoint(
        id=f"{session_id}_v{version}",
        session_id=session_id,
        data=data,
        version=version,
        parent_id=latest.id if latest else "",
        message=message
    )

    self._save(checkpoint)
    return checkpoint.id
```

#### 2.2 事件驱动架构

```python
class DataEvent(str, Enum):
    """数据事件"""
    AGENT_CREATED = "agent.created"
    RUN_STARTED = "run.started"
    RUN_COMPLETED = "run.completed"
    CHECKPOINT_SAVED = "checkpoint.saved"
    WORKSPACE_CREATED = "workspace.created"

class EventBus:
    """事件总线"""

    def __init__(self):
        self._handlers: Dict[DataEvent, List[Callable]] = {}

    def subscribe(self, event: DataEvent, handler: Callable):
        if event not in self._handlers:
            self._handlers[event] = []
        self._handlers[event].append(handler)

    def publish(self, event: DataEvent, data: Dict):
        for handler in self._handlers.get(event, []):
            handler(data)

    def unsubscribe(self, event: DataEvent, handler: Callable):
        if event in self._handlers:
            self._handlers[event].remove(handler)

# 使用示例
event_bus = EventBus()

# 订阅事件
event_bus.subscribe(DataEvent.RUN_COMPLETED,
                    lambda d: print(f"Run completed: {d['run_id']}"))

# 自动发布事件
@dataclass
class DataStore:
    def __init__(self):
        self.events = EventBus()

    def save_run(self, run: AgentRunData):
        # 保存数据
        self._save(run)
        # 发布事件
        self.events.publish(DataEvent.RUN_COMPLETED,
                          {"run_id": run.run_id, "status": run.status})
```

---

### Phase 3: 企业级增强 (P2)

#### 3.1 物理隔离租户

```python
class TenantDataStore(DataStore):
    """租户专属数据存储"""

    def __init__(self, tenant_id: str, base_dir: str = ".young"):
        # 物理隔离目录
        self.data_dir = Path(base_dir) / "tenants" / tenant_id
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # 每个租户独立数据库
        self.db_path = self.data_dir / "data.db"
        self._init_unified_schema()

# 访问控制
class TenantAccessControl:
    """租户访问控制"""

    def __init__(self, store: TenantDataStore):
        self.store = store
        self.tenant_id = store.tenant_id

    def check_access(self, user_id: str, resource_id: str) -> bool:
        """验证用户对资源的访问权限"""
        # 检查用户是否属于租户
        # 检查资源是否属于租户
        return True
```

#### 3.2 缓存层

```python
from functools import lru_cache

class CachedDataStore(DataStore):
    """带缓存的数据存储"""

    def __init__(self, *args, cache_size: int = 100, **kwargs):
        super().__init__(*args, **kwargs)
        self._cache: Dict[str, Any] = {}
        self._cache_order: List[str] = []
        self._max_cache = cache_size

    def get_agent(self, agent_id: str) -> AgentData:
        # 先查缓存
        if agent_id in self._cache:
            return self._cache[agent_id]

        # 缓存未命中，查询数据库
        agent = super().get_agent(agent_id)

        # 存入缓存
        self._add_to_cache(agent_id, agent)

        return agent

    def _add_to_cache(self, key: str, value: Any):
        if len(self._cache) >= self._max_cache:
            # LRU 淘汰
            oldest = self._cache_order.pop(0)
            del self._cache[oldest]

        self._cache[key] = value
        self._cache_order.append(key)
```

---

## 实施计划

### Sprint 1: 统一数据层 (2周)

| 任务 | 负责人 | 验收标准 |
|------|--------|----------|
| 创建 DataStore 类 | AI | 统一入口可用 |
| 迁移现有数据 | AI | 数据不丢失 |
| 事务支持 | AI | 原子性验证通过 |
| 合并 Workspace/Isolation | AI | 功能等价 |

### Sprint 2: 增强功能 (2周)

| 任务 | 负责人 | 验收标准 |
|------|--------|----------|
| 版本控制 | AI | 可创建/回滚版本 |
| 事件总线 | AI | 事件正常触发 |
| Webhook 支持 | AI | 外部通知可用 |

### Sprint 3: 企业级 (2周)

| 任务 | 负责人 | 验收标准 |
|------|--------|----------|
| 租户物理隔离 | AI | 目录级别隔离 |
| 缓存层 | AI | 命中率 > 50% |
| 性能优化 | AI | 查询 < 100ms |

---

## 风险与回退

### 风险

| 风险 | 概率 | 影响 | 缓解 |
|------|------|------|------|
| 数据迁移失败 | 中 | 高 | 保留原数据，先测试 |
| API 破坏性变更 | 高 | 中 | 兼容层 |
| 性能退化 | 低 | 中 | 监控 + 回退 |

### 回退计划

1. 保留原模块作为兼容层
2. 数据迁移前完整备份
3. A/B 测试验证

---

## 验收标准

### 功能验收

- [ ] DataStore 统一入口可用
- [ ] 所有现有 API 兼容
- [ ] 事务保证生效
- [ ] Workspace/Isolation 合并完成

### 性能验收

- [ ] 单次查询 < 50ms
- [ ] 批量操作 < 500ms
- [ ] 缓存命中率 > 50%

### 稳定性验收

- [ ] 100% 单元测试通过
- [ ] 集成测试通过
- [ ] 压力测试通过

---

*创建日期: 2026-03-06*
*版本: 2.0*

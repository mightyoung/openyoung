# 数据系统改进 - 详细实施计划

## 目标

基于 v2.0 改进方案，制定可执行的详细实施计划，坚持"以抄为主，以写为辅"原则。

---

## 策略: 复用现有库

| 功能 | 推荐库 | 原因 |
|------|--------|------|
| 事件总线 | `blinker` (1.5MB) | Flask 官方，轻量 |
| 缓存 | `cachetools` | Python 标准，高效 |
| ORM | `sqlalchemy` | 成熟稳定 |
| 版本控制 | SQLite 自身 | 内置支持 |

---

## Phase 1: 统一数据层 (Sprint 1-2)

### 1.1 创建 DataStore 统一入口

**策略**: 直接复用 sqlalchemy 作为 ORM 层

```python
# 现有库: sqlalchemy
# pip install sqlalchemy
from sqlalchemy import create_engine, Column, String, Integer, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
```

**实施步骤**:

| 步骤 | 任务 | 依赖 |
|------|------|------|
| 1.1.1 | 安装 sqlalchemy | - |
| 1.1.2 | 创建统一 ORM Model | sqlalchemy |
| 1.1.3 | 实现基础 CRUD | - |
| 1.1.4 | 添加兼容性包装器 | 现有 datacenter.py |

**代码参考** (抄自 LangChain):
```python
# langchain/storage.py 模式
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

class SQLStore:
    def __init__(self, connection_string: str):
        self.engine = create_engine(connection_string)
        self.SessionLocal = sessionmaker(bind=self.engine)

    def save(self, key: str, value: dict):
        with self.SessionLocal() as session:
            # 保存逻辑
            pass
```

### 1.2 事务支持

**策略**: 直接使用 SQLite 内置事务

```python
# SQLite 原生支持，无需额外库
with sqlite3.connect(db_path) as conn:
    conn.execute("BEGIN IMMEDIATE")
    try:
        # 多个操作
        conn.commit()
    except:
        conn.rollback()
        raise
```

### 1.3 Workspace/Isolation 合并

**策略**: 复用现有 workspace.py，仅做整合

| 任务 | 操作 |
|------|------|
| 1.3.1 | 迁移隔离逻辑到 Workspace |
| 1.3.2 | 移除 isolation.py 独立模块 |
| 1.3.3 | 更新引用 |

---

## Phase 2: 增强功能 (Sprint 3-4)

### 2.1 数据版本控制

**策略**: 使用 SQLite 表实现，参考 Git 思想

```sql
-- 直接抄 Git 分支模型
CREATE TABLE versions (
    id TEXT PRIMARY KEY,
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    version INTEGER NOT NULL,
    parent_id TEXT,
    data TEXT NOT NULL,
    message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_versions_entity ON versions(entity_type, entity_id);
```

### 2.2 事件驱动架构

**策略**: 使用 `blinker` 库 (Flask 内置)

```python
# 安装: pip install blinker
from blinker import signal

# 定义信号
checkpoint_saved = signal('checkpoint.saved')
run_completed = signal('run.completed')

# 订阅
def on_checkpoint_saved(sender, **kw):
    print(f"Checkpoint saved: {kw.get('checkpoint_id')}")

checkpoint_saved.connect(on_checkpoint_saved)

# 发布
checkpoint_saved.send(self, checkpoint_id=cp_id, data=data)
```

### 2.3 缓存层

**策略**: 使用 `cachetools` 库

```python
# 安装: pip install cachetools
from cachetools import LRUCache, cached

class CacheManager:
    def __init__(self, maxsize: int = 100):
        self._cache = LRUCache(maxsize=maxsize)

    @cached(cache=_cache)
    def get_agent(self, agent_id: str):
        # 实际查询
        return self._fetch_agent(agent_id)
```

---

## Phase 3: 企业级 (Sprint 5-6)

### 3.1 物理隔离

**策略**: 目录级别隔离 + 文件系统权限

```python
# 复用 Path 和权限检查
from pathlib import Path
import os

class Tenant隔离:
    @staticmethod
    def get_tenant_dir(tenant_id: str, base: Path) -> Path:
        return base / "tenants" / tenant_id
```

### 3.2 性能优化

**策略**: 使用 sqlalchemy 索引 + 查询优化

```sql
-- 添加复合索引
CREATE INDEX idx_runs_user_agent ON runs(user_id, agent_id);
CREATE INDEX idx_runs_time_status ON runs(created_at, status);
```

---

## 详细任务清单

### Sprint 1 (Week 1-2): 基础搭建

| ID | 任务 | 库 | 估计 |
|----|------|-----|------|
| T1.1 | 安装依赖 (sqlalchemy, blinker, cachetools) | pip | 10min |
| T1.2 | 创建统一 Model 基类 | sqlalchemy | 1h |
| T1.3 | 实现 DataStore 基础 CRUD | - | 2h |
| T1.4 | 迁移现有 datacenter.py 接口 | - | 2h |
| T1.5 | 编写单元测试 | pytest | 1h |

### Sprint 2 (Week 3-4): 完善 DataStore

| ID | 任务 | 库 | 估计 |
|----|------|-----|------|
| T2.1 | 添加事务支持 | sqlite3 | 1h |
| T2.2 | 合并 Workspace 到 DataStore | - | 2h |
| T2.3 | 添加兼容性包装器 | - | 1h |
| T2.4 | 集成测试 | pytest | 1h |

### Sprint 3 (Week 5-6): 版本控制

| ID | 任务 | 库 | 估计 |
|----|------|-----|------|
| T3.1 | 设计版本表结构 | SQL | 30min |
| T3.2 | 实现 VersionedCheckpoint | - | 2h |
| T3.3 | 添加版本回滚方法 | - | 1h |
| T3.4 | 测试版本功能 | pytest | 1h |

### Sprint 4 (Week 7-8): 事件驱动

| ID | 任务 | 库 | 估计 |
|----|------|-----|------|
| T4.1 | 集成 blinker 信号 | blinker | 1h |
| T4.2 | 定义核心事件 | - | 30min |
| T4.3 | 添加事件订阅示例 | - | 1h |
| T4.4 | 文档和测试 | pytest | 1h |

### Sprint 5 (Week 9-10): 企业级

| ID | 任务 | 库 | 估计 |
|----|------|-----|------|
| T5.1 | 实现租户物理隔离 | - | 2h |
| T5.2 | 添加缓存层 | cachetools | 1h |
| T5.3 | 性能优化 | SQL | 1h |

### Sprint 6 (Week 11-12): 完善

| ID | 任务 | 库 | 估计 |
|----|------|-----|------|
| T6.1 | 完整集成测试 | pytest | 2h |
| T6.2 | 文档更新 | - | 1h |
| T6.3 | 性能基准测试 | - | 1h |

---

## 依赖安装

```bash
pip install sqlalchemy blinker cachetools
```

---

## 风险控制

| 风险 | 缓解措施 |
|------|----------|
| sqlalchemy 学习曲线 | 只用基础功能 |
| 破坏现有 API | 保留原接口，内部调用新实现 |
| 数据迁移丢失 | 先备份，再迁移 |

---

## 里程碑

| 日期 | 里程碑 |
|------|---------|
| Week 2 | DataStore 可用 |
| Week 4 | 统一入口完成 |
| Week 6 | 版本控制完成 |
| Week 8 | 事件驱动完成 |
| Week 10 | 企业级完成 |
| Week 12 | 完整测试通过 |

---

*计划日期: 2026-03-06*

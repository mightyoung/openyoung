# OpenYoung 数据系统轻量化实施计划 v4.0

## 核心理念：数据即资产

**定位**：AI Agent 发现与部署平台
**原则**：轻量化 + 数据资产化
**策略**：以抄为主，以写为辅，直接使用可靠开源库

---

## 一、当前状态评估

### 已实现模块
| 模块 | 状态 | 是否保留 |
|------|------|----------|
| DataStore | ✅ 完整 | ✅ 核心保留 |
| SqliteCheckpointSaver | ✅ 完整 | ✅ 核心保留 |
| Agent 角色系统 | ⚠️ 过重 | ⚠️ 简化 |
| MessageBus | ⚠️ 过重 | ⚠️ 简化为事件 |
| TenantDataStore | ✅ 完整 | ✅ 可选保留 |
| CachedDataStore | ✅ 完整 | ⚠️ 简化 |

### 问题分析
1. **Agent 角色系统**：6种角色过于复杂，轻量化产品不需要
2. **MessageBus**：完整消息总线过重，可用简单事件替代
3. **多层缓存**：LRU+TTL 缓存对轻量化产品非必需

---

## 二、架构设计（轻量化版）

```
┌─────────────────────────────────────────────────┐
│              OpenYoung Data Layer              │
├─────────────────────────────────────────────────┤
│  ┌───────────────────────────────────────────┐ │
│  │           DataStore (核心)                │ │
│  │  - SQLite + SQLAlchemy                    │ │
│  │  - 统一 CRUD + 版本控制                   │ │
│  │  - 事件驱动 (blinker)                    │ │
│  └───────────────────────────────────────────┘ │
│                       │                         │
│           ┌──────────┼──────────┐             │
│           ▼          ▼          ▼             │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────┐ │
│  │ Checkpoint  │ │ RunTracker  │ │ Stats   │ │
│  │ (Lang │ (执行追踪)  Graph) │ │ │ (数据)  │ │
│  └─────────────┘ └─────────────┘ └─────────┘ │
│                                             │
│  ┌─────────────────────────────────────────┐ │
│  │         DataWarehouse (数据资产化)       │ │
│  │  - 统计分析 | 导出 | 可视化              │ │
│  └─────────────────────────────────────────┘ │
└─────────────────────────────────────────────────┘
```

---

## 三、实施计划

### Phase 1: 核心数据层（1周）

#### 1.1 完善 DataStore 事件系统

**目标**：确保事件系统完整可用

**实现**（复用现有代码）：
```python
# 已有事件信号定义
checkpoint_saved = signal('checkpoint.saved')
run_started = signal('run.started')
run_completed = signal('run.completed')
workspace_created = signal('workspace.created')

# 监听示例
def on_run_completed(sender, run_id, **kwargs):
    # 记录统计数据
    pass

run_completed.connect(on_run_completed)
```

**任务**：
- [ ] 添加更多事件信号（agent_created, task_completed 等）
- [ ] 添加事件历史记录表
- [ ] 单元测试

#### 1.2 实现 RunTracker（运行追踪）

**目标**：收集 Agent 运行数据，形成数据资产

**依赖**：复用现有 store.py

**实现**：
```python
# src/datacenter/run_tracker.py
from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from datetime import datetime

@dataclass
class RunRecord:
    """运行记录"""
    run_id: str
    agent_id: str
    task: str
    status: str  # running, success, failed
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    duration: Optional[float] = None
    input_tokens: int = 0
    output_tokens: int = 0
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
```

**数据采集**：
- 任务开始/结束时间
- 执行时长
- Token 消耗
- 成功/失败状态
- 错误信息

**任务**：
- [ ] 创建 `src/datacenter/run_tracker.py`
- [ ] 实现 RunRecord 数据结构
- [ ] 实现追踪方法（start, complete, fail）
- [ ] 集成到 DataStore
- [ ] 单元测试

#### 1.3 完善 Checkpoint 接口

**目标**：确保 LangGraph 风格接口完整

**已实现**（确认可用）：
- CheckpointSaver Protocol
- SqliteCheckpointSaver

**任务**：
- [ ] 验证现有实现
- [ ] 添加 checkpoint 事件触发
- [ ] 单元测试

---

### Phase 2: 数据资产化（1周）

#### 2.1 数据统计分析

**目标**：从运行数据中提取有价值的信息

**依赖**：RunTracker

**实现**：
```python
# src/datacenter/analytics.py
from typing import Dict, List, Any
from datetime import datetime, timedelta

class DataAnalytics:
    """数据分析"""

    def get_agent_stats(self, agent_id: str, days: int = 7) -> Dict:
        """获取 Agent 统计数据"""
        # 总运行次数
        # 成功率
        # 平均执行时间
        # Token 消耗

    def get_task_stats(self, task_type: str, days: int = 7) -> Dict:
        """获取任务类型统计"""
        # 任务数量
        # 成功率
        # 常见错误

    def get_trends(self, metric: str, days: int = 30) -> List[Dict]:
        """获取趋势数据"""
        # 时间序列数据
```

**任务**：
- [ ] 创建 `src/datacenter/analytics.py`
- [ ] 实现统计数据方法
- [ ] 实现趋势分析
- [ ] 单元测试

#### 2.2 数据导出功能

**目标**：支持数据导出，形成可流通的数据资产

**格式**：JSON, CSV

**实现**：
```python
# src/datacenter/exporter.py
import json
import csv
from pathlib import Path
from typing import List, Dict, Any

class DataExporter:
    """数据导出器"""

    def export_runs(self, output_path: str, format: str = "json") -> bool:
        """导出运行记录"""

    def export_agents(self, output_path: str, format: str = "json") -> bool:
        """导出 Agent 数据"""

    def export_checkpoints(self, output_path: str) -> bool:
        """导出检查点"""

    def export_full(self, output_dir: str) -> Dict[str, str]:
        """导出所有数据"""
        # 返回导出的文件路径
```

**任务**：
- [ ] 创建 `src/datacenter/exporter.py`
- [ ] 实现 JSON 导出
- [ ] 实现 CSV 导出
- [ ] 单元测试

#### 2.3 数据可视化支持

**目标**：为前端提供数据查询接口

**实现**：
```python
# 返回格式便于前端展示
def get_dashboard_data(self) -> Dict:
    """获取仪表盘数据"""
    return {
        "summary": {
            "total_agents": 10,
            "total_runs": 100,
            "success_rate": 0.85,
            "avg_duration": 5.2
        },
        "charts": {
            "runs_per_day": [...],
            "success_rate_trend": [...]
        }
    }
```

**任务**：
- [ ] 添加 dashboard 数据方法
- [ ] 支持时间范围过滤
- [ ] 单元测试

---

### Phase 3: 高级特性（可选）

#### 3.1 任务恢复（基于 Checkpoint）

**目标**：支持任务中断后恢复

**实现**：复用 SqliteCheckpointSaver

```python
def resume_task(self, checkpoint_id: str) -> Dict:
    """从检查点恢复任务"""
    checkpoint = self.checkpoint_saver.get_by_id(checkpoint_id)
    return checkpoint["state"]
```

#### 3.2 租户隔离（可选）

**目标**：支持多用户场景

**复用**：已有 TenantDataStore

```python
def get_tenant_store(tenant_id: str) -> TenantDataStore:
    """获取租户数据存储"""
    return TenantDataStore(tenant_id)
```

#### 3.3 数据压缩与归档

**目标**：优化存储

**实现**：
```python
def archive_old_data(self, before_date: datetime) -> int:
    """归档旧数据"""
    # 压缩历史数据
    # 移动到归档表
```

---

## 四、开源库依赖

### 现有依赖
```bash
# 已有
pip install sqlalchemy blinker cachetools
```

### 建议新增
```bash
# 数据分析（可选）
pip install pandas  # 数据处理

# 导出功能（复用标准库，无需额外依赖）
# JSON: 内置 json
# CSV: 内置 csv
```

---

## 五、代码复用策略

### 直接使用的开源代码

| 功能 | 来源 | 复用方式 |
|------|------|----------|
| SQLAlchemy 模型 | sqlalchemy | 依赖库直接使用 |
| 事件信号 | blinker | 依赖库直接使用 |
| LRU 缓存 | cachetools | 可选使用 |
| Checkpoint 接口 | LangGraph | 参考接口实现 |

### 借鉴的开源项目

| 项目 | 借鉴点 |
|------|--------|
| LangGraph | Checkpoint 接口设计 |
| AutoGen | 运行记录数据结构 |
| LangSmith | 数据分析维度 |

---

## 六、文件结构

```
src/datacenter/
├── __init__.py          # 统一导出
├── store.py             # DataStore (已有)
├── checkpoint.py        # Checkpoint (已有)
├── run_tracker.py       # 新建：运行追踪
├── analytics.py         # 新建：数据分析
├── exporter.py         # 新建：数据导出
├── models.py            # 数据模型 (已有)
└── warehouse.py        # 数据仓库 (已有)
```

---

## 七、验收标准

### Phase 1
- [ ] DataStore 事件系统完整可用
- [ ] RunTracker 记录运行数据
- [ ] Checkpoint 接口验证通过

### Phase 2
- [ ] DataAnalytics 统计正确
- [ ] DataExporter 导出功能正常
- [ ] Dashboard 数据接口可用

### Phase 3（可选）
- [ ] 任务恢复功能可用
- [ ] 租户隔离可选开启
- [ ] 数据归档功能正常

---

## 八、使用示例

### 示例 1: 运行追踪

```python
from src.datacenter import DataStore, RunTracker

store = DataStore()
tracker = RunTracker(store)

# 开始追踪
run_id = tracker.start_run(
    agent_id="agent-001",
    task="爬取小红书热榜"
)

# ... 执行任务 ...

# 完成追踪
tracker.complete_run(
    run_id=run_id,
    status="success",
    output_tokens=1500
)
```

### 示例 2: 数据分析

```python
from src.datacenter.analytics import DataAnalytics

analytics = DataAnalytics()

# 获取 Agent 统计
stats = analytics.get_agent_stats("agent-001", days=7)
print(f"成功率: {stats['success_rate']}")
print(f"平均耗时: {stats['avg_duration']}s")
```

### 示例 3: 数据导出

```python
from src.datacenter.exporter import DataExporter

exporter = DataExporter()

# 导出所有数据
files = exporter.export_full("backup/2026-03-06")
print(files)
# {'runs': 'backup/2026-03-06/runs.json', ...}
```

---

## 九、风险控制

| 风险 | 缓解措施 |
|------|----------|
| 破坏现有功能 | 先测试，保留旧接口 |
| 性能下降 | 使用索引，必要时加缓存 |
| 复杂度增加 | 保持轻量化，不过度设计 |

---

*版本: 4.0*
*更新日期: 2026-03-06*
*核心理念: 数据即资产 | 策略: 以抄为主，以写为辅*

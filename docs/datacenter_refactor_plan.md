# Datacenter.py 重构计划

## 目标

将 `datacenter.py` (638+ 行) 拆分为独立模块，保持向后兼容。

## 当前结构

```
datacenter.py
├── TraceStatus (Enum)
├── TraceRecord (dataclass)
├── TraceCollector (~280 行)
├── BudgetController (~25 行)
├── PatternDetector (~30 行)
├── MemoryItem (dataclass)
├── EpisodicMemory (~30 行)
├── SemanticMemory (~30 行)
├── WorkingMemory (~30 行)
├── Checkpoint (~15 行)
├── CheckpointManager (~180 行)
└── DataCenter (~200 行)
```

## 重构方案

### 方案: 渐进式拆分

创建独立模块，从 datacenter.py 导入并重新导出：

```
src/datacenter/
├── datacenter.py          # 入口，保持向后兼容
├── tracing/              # 新建追踪模块
│   ├── __init__.py
│   └── collector.py     # TraceCollector
├── memory/               # 新建内存模块
│   ├── __init__.py
│   ├── episodic.py     # EpisodicMemory
│   ├── semantic.py     # SemanticMemory
│   └── working.py      # WorkingMemory
├── budget/              # 新建预算模块
│   ├── __init__.py
│   └── controller.py   # BudgetController
└── checkpoint/          # 新建检查点模块
    ├── __init__.py
    └── manager.py      # CheckpointManager
```

## 实施步骤

### Phase 1: 创建新模块结构 (不破坏现有代码)

1. 创建 `src/datacenter/tracing/collector.py`
2. 创建 `src/datacenter/memory/*.py`
3. 创建 `src/datacenter/budget/controller.py`
4. 创建 `src/datacenter/checkpoint/manager.py`

### Phase 2: 更新 datacenter.py

```python
# datacenter.py
from .tracing.collector import TraceCollector
from .memory import EpisodicMemory, SemanticMemory, WorkingMemory
from .budget.controller import BudgetController
from .checkpoint.manager import CheckpointManager

# 保持原有导出
__all__ = [
    'TraceCollector',
    'BudgetController',
    ...
]
```

### Phase 3: 更新导入

更新所有使用 `from src.datacenter.datacenter import` 的文件。

## 向后兼容

确保以下导入仍然有效：
```python
from src.datacenter import DataCenter  # 通过 __init__.py
from src.datacenter.datacenter import DataCenter  # 直接导入
```

## 时间估算

- Phase 1: 2小时
- Phase 2: 1小时
- Phase 3: 1小时

总计: 4小时

## 风险控制

1. 先在测试环境验证
2. 保持原有类的完整功能
3. 添加单元测试覆盖

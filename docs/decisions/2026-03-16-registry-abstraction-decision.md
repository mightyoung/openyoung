# 决策文档: 重复注册模式重构

> 日期: 2026-03-16
> 问题: 多个重复的注册表实现
> 决策: B - 抽象基类

---

## 1. 问题背景

现状存在多个类似的注册表实现：

```
registry.py (package_manager)
registry/registry.py (hub)
base_registry.py
subagent_registry.py
template_registry.py
```

## 2. 调研结果

### 2.1 行业最佳实践

| 来源 | 关键洞见 |
|------|----------|
| Martin Fowler | 单一职责 + 依赖倒置 |
| Django | Model Registry 模式 |
| FastAPI | 依赖注入容器 |

### 2.2 现状分析

| 注册表 | 位置 | 功能 |
|--------|------|------|
| registry.py | package_manager | Agent 注册 |
| registry/registry.py | hub | Agent 注册(重复) |
| base_registry.py | 通用基类 | 未充分利用 |
| subagent_registry.py | agents | 子Agent注册 |
| template_registry.py | 模板 | 模板注册 |

## 3. 决策详情

### 3.1 架构设计

```
┌─────────────────────────────────────────────────────────────────┐
│                    注册表架构                                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                 BaseRegistry[T]                           │   │
│  │  (泛型抽象基类)                                           │   │
│  │                                                           │   │
│  │   + register(key, item)                                 │   │
│  │   + unregister(key)                                     │   │
│  │   + get(key) → T                                        │   │
│  │   + list() → list[T]                                   │   │
│  │   + exists(key) → bool                                 │   │
│  │   + search(query) → list[T]                            │   │
│  └──────────────────────────────────────────────────────────┘   │
│           │                  │                │                   │
│           ▼                  ▼                ▼                   │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐     │
│  │ AgentRegistry │  │TemplateRegistry│  │SkillRegistry │     │
│  │               │  │               │  │               │     │
│  │ - agents      │  │ - templates   │  │ - skills     │     │
│  │ - metadata    │  │ - versions    │  │ - schemas    │     │
│  └───────────────┘  └───────────────┘  └───────────────┘     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 核心实现

```python
# src/core/registry/base.py
from typing import TypeVar, Generic, Optional, Callable
from dataclasses import dataclass
from datetime import datetime

T = TypeVar('T')

@dataclass
class RegistryItem:
    """注册项元数据"""
    key: str
    item: any
    created_at: datetime
    updated_at: datetime
    version: str = "1.0.0"
    metadata: dict = None

class BaseRegistry(Generic[T]):
    """泛型注册表基类"""

    def __init__(self, name: str):
        self.name = name
        self._items: dict[str, RegistryItem] = {}
        self._listeners: list[Callable] = []

    def register(
        self,
        key: str,
        item: T,
        metadata: dict = None,
        version: str = "1.0.0",
    ) -> None:
        """注册项"""
        now = datetime.now()
        self._items[key] = RegistryItem(
            key=key,
            item=item,
            created_at=now,
            updated_at=now,
            version=version,
            metadata=metadata or {},
        )
        self._notify("register", key, item)

    def unregister(self, key: str) -> bool:
        """注销项"""
        if key in self._items:
            item = self._items.pop(key)
            self._notify("unregister", key, item)
            return True
        return False

    def get(self, key: str) -> Optional[T]:
        """获取项"""
        registry_item = self._items.get(key)
        return registry_item.item if registry_item else None

    def list(self) -> list[T]:
        """列出所有项"""
        return [ri.item for ri in self._items.values()]

    def exists(self, key: str) -> bool:
        """检查存在"""
        return key in self._items

    def search(self, query: str) -> list[T]:
        """搜索"""
        # 子类可重写实现更复杂的搜索
        query_lower = query.lower()
        return [
            ri.item for ri in self._items.values()
            if query_lower in str(ri.item).lower()
        ]

    def _notify(self, event: str, key: str, item: any):
        """通知监听器"""
        for listener in self._listeners:
            listener(event, key, item)

    def add_listener(self, listener: Callable):
        """添加监听器"""
        self._listeners.append(listener)
```

### 3.3 具体注册表实现

```python
# src/core/registry/agent.py
from dataclasses import dataclass

@dataclass
class AgentMetadata:
    """Agent 元数据"""
    name: str
    description: str
    capabilities: list[str]
    version: str

class AgentRegistry(BaseRegistry[AgentMetadata]):
    """Agent 注册表"""

    def __init__(self):
        super().__init__("agents")

    def register_agent(
        self,
        name: str,
        description: str,
        capabilities: list[str],
    ):
        """注册 Agent"""
        metadata = AgentMetadata(
            name=name,
            description=description,
            capabilities=capabilities,
            version="1.0.0",
        )
        self.register(name, metadata)

    def get_by_capability(self, capability: str) -> list[AgentMetadata]:
        """按能力查找"""
        return [
            m for m in self.list()
            if capability in m.capabilities
        ]
```

## 4. 实施计划

| 阶段 | 任务 | 文件 |
|------|------|------|
| Phase 1 | 抽象基类 | `src/core/registry/base.py` |
| Phase 2 | Agent注册表 | `src/core/registry/agent.py` |
| Phase 3 | 其他注册表 | 逐步迁移 |
| Phase 4 | 移除重复 | 删除旧注册表 |

## 5. 风险与缓解

| 风险 | 影响 | 缓解 |
|------|------|------|
| 破坏现有代码 | 运行时错误 | 渐进迁移，保留别名 |
| 功能减少 | 某些功能丢失 | 逐个迁移验证 |

---

## 6. 参考实现

- Django Registry: https://docs.djangoproject.com/en/stable/ref/applications/
- FastAPI Dependency Injection: https://fastapi.tiangolo.com/tutorial/dependencies/

---

**决策人**: Claude + User
**决策日期**: 2026-03-16
**状态**: 已批准

# 决策文档: 核心接口抽象

> 日期: 2026-03-16
> 问题: 缺乏接口抽象
> 决策: B - 核心抽象

---

## 1. 问题背景

现状直接依赖具体实现：

```python
# 现状 - 直接依赖
from src.datacenter.sqlite_storage import SQLiteStorage

# 建议 - 通过接口
from src.datacenter.base_storage import BaseStorage
```

## 2. 调研结果

### 2.1 行业最佳实践

| 来源 | 关键洞见 |
|------|----------|
| Martin Fowler | 依赖倒置原则 - 面向接口编程 |
| Python typing | Protocol 实现 Duck Typing |
| Django | BaseValidator, BaseSerializer 模式 |

### 2.2 需要抽象的核心模块

| 模块 | 抽象接口 | 现状 |
|------|----------|------|
| Storage | BaseStorage | SQLiteStorage |
| Agent | BaseAgent | YoungAgent |
| Evaluator | BaseEvaluator | LLMJudge |
| Sandbox | BaseSandbox | DockerSandbox |
| LLM Client | BaseLLMClient | OpenAIClient |

## 3. 决策详情

### 3.1 架构设计

```
┌─────────────────────────────────────────────────────────────────┐
│                    接口层次结构                                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                     业务层                                 │   │
│  │                                                           │   │
│  │   young_agent.py  │  task_eval.py  │  hub.py           │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              │                                   │
│                              ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                     接口层 (Protocol)                      │   │
│  │                                                           │   │
│  │   BaseAgent   BaseStorage   BaseEvaluator   BaseSandbox │   │
│  │       │           │            │            │            │   │
│  │       ▼           ▼            ▼            ▼            │   │
│  │   (Protocol)  (Protocol)   (Protocol)   (Protocol)       │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              │                                   │
│                              ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                     实现层                                  │   │
│  │                                                           │   │
│  │   YoungAgent   SQLiteStorage   LLMJudge   DockerSandbox │   │
│  │   ClaudeAgent  PostgresStorage  CodeEval   PodmanSandbox │   │
│  │                                                         │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 Protocol 接口定义

```python
# src/core/interfaces/storage.py
from typing import Protocol, AsyncIterator
from datetime import datetime
import uuid

class BaseStorage(Protocol):
    """存储接口"""

    async def save(self, key: str, value: dict) -> None:
        """保存数据"""
        ...

    async def get(self, key: str) -> dict | None:
        """获取数据"""
        ...

    async def delete(self, key: str) -> bool:
        """删除数据"""
        ...

    async def list(self, prefix: str = "") -> list[str]:
        """列出数据"""
        ...

    async def exists(self, key: str) -> bool:
        """检查存在"""
        ...
```

```python
# src/core/interfaces/agent.py
from typing import Protocol, Any
from abc import abstractmethod

class AgentCapability(Protocol):
    """Agent 能力接口"""

    @abstractmethod
    async def execute(self, task: str, context: dict = None) -> dict[str, Any]:
        """执行任务"""
        ...

    @abstractmethod
    async def validate(self, input_data: dict) -> bool:
        """验证输入"""
        ...
```

```python
# src/core/interfaces/evaluator.py
from typing import Protocol, Any

class EvaluationResult:
    """评估结果"""
    score: float
    passed: bool
    feedback: str
    details: dict

class BaseEvaluator(Protocol):
    """评估器接口"""

    async def evaluate(
        self,
        input_data: Any,
        expected: Any,
        criteria: dict = None,
    ) -> EvaluationResult:
        """评估"""
        ...

    async def batch_evaluate(
        self,
        inputs: list[Any],
        expecteds: list[Any],
    ) -> list[EvaluationResult]:
        """批量评估"""
        ...
```

### 3.3 依赖注入

```python
# src/core/di.py
from typing import TypeVar, Type, Callable
from dataclasses import dataclass

T = TypeVar('T')

@dataclass
class Dependency:
    """依赖项"""
    interface: Type
    implementation: Type
    factory: Callable | None = None

class Container:
    """依赖注入容器"""

    def __init__(self):
        self._dependencies: dict[Type, Dependency] = {}
        self._singletons: dict[Type, object] = {}

    def register(
        self,
        interface: Type[T],
        implementation: Type[T] = None,
        factory: Callable[[], T] = None,
        singleton: bool = True,
    ):
        """注册依赖"""
        self._dependencies[interface] = Dependency(
            interface=interface,
            implementation=implementation,
            factory=factory,
        )
        if singleton:
            self._singletons[interface] = None

    def resolve(self, interface: Type[T]) -> T:
        """解析依赖"""
        dep = self._dependencies.get(interface)
        if not dep:
            raise ValueError(f"No dependency registered for {interface}")

        # 返回单例或创建新实例
        if interface in self._singletons:
            if self._singletons[interface] is None:
                self._singletons[interface] = self._create_instance(dep)
            return self._singletons[interface]
        return self._create_instance(dep)

    def _create_instance(self, dep: Dependency) -> T:
        """创建实例"""
        if dep.factory:
            return dep.factory()
        return dep.implementation()
```

### 3.4 使用示例

```python
# src/agents/young_agent.py
class YoungAgent:
    """使用依赖注入的 Agent"""

    def __init__(
        self,
        storage: BaseStorage,  # 接口注入
        evaluator: BaseEvaluator = None,
        sandbox: BaseSandbox = None,
    ):
        self.storage = storage
        self.evaluator = evaluator
        self.sandbox = sandbox
```

## 4. 实施计划

| 阶段 | 任务 | 文件 |
|------|------|------|
| Phase 1 | 接口定义 | `src/core/interfaces/*.py` |
| Phase 2 | 依赖注入 | `src/core/di.py` |
| Phase 3 | 迁移核心模块 | 逐步迁移 |
| Phase 4 | 移除直接依赖 | 重构导入 |

## 5. 风险与缓解

| 风险 | 影响 | 缓解 |
|------|------|------|
| 过度抽象 | 复杂难懂 | 只抽象核心模块 |
| 性能开销 | 微小 | 减少函数调用层级 |

---

## 6. 参考实现

- Python Protocols: https://mypy.readthedocs.io/en/stable/more_types.html
- Django ORM: https://docs.djangoproject.com/en/stable/ref/models/instances/

---

**决策人**: Claude + User
**决策日期**: 2026-03-16
**状态**: 已批准

# OpenYoung Phase 11 详细执行计划

> 基于 Martin Fowler, Michael Feathers, Robert C. Martin, Kent Beck 最佳实践
> 日期: 2026-03-08

---

## 专家方法论

### Martin Fowler (重构)

> "Refactoring is a controlled technique for improving the design of an existing code base."

**核心理念**:
- 小步进行，每步可逆
- 每次重构后运行测试
- 代码味道是改进的起点

### Michael Feathers (遗留代码)

> "A legacy system is one that works, but that we are afraid to change."

**核心理念**:
- 围栏法 (Strangler Fig Pattern)
- 添加测试是改变遗留代码的第一步
- 依赖注入是解耦的关键

### Robert C. Martin (Clean Code)

> "Clean code always looks like it was written by someone who cares."

**核心理念**:
- SOLID 原则
- 函数应该小而专注
- 单一职责原则 (SRP)

### Kent Beck (TDD)

> "Make it work, make it right, make it fast."

**核心理念**:
- 优先级：可用性 → 正确性 → 性能
- 测试驱动开发

---

## 任务 1: young_agent.py 拆分

### 当前状态

```
src/agents/young_agent.py: 1,463 行
```

### 问题

- 56KB 单文件
- 25 个定义 (1 class, 24 funcs)
- 配置硬编码 (25-100行)
- 评分权重散落
- 阈值配置散落

### 拆分策略 (围栏法)

**步骤 1: 创建组件目录**
```bash
mkdir -p src/agents/components
```

**步骤 2: 提取配置类**
```python
# src/agents/components/config.py
from dataclasses import dataclass
from typing import Dict

@dataclass
class AgentConfig:
    """Agent 配置"""
    name: str
    model: str
    temperature: float = 0.7
    max_tokens: int = 2000
    mode: str = "primary"

# 从 young_agent.py 移出的配置
TASK_TYPE_WEIGHTS = {
    "coding": {"base_score": 0.6, "completion_rate": 0.3, "efficiency": 0.1},
    "general": {"base_score": 0.5, "completion_rate": 0.3, "efficiency": 0.2},
    # ...
}

DEFAULT_WEIGHTS = {
    "base_score": 0.5,
    "completion_rate": 0.3,
    "efficiency": 0.2,
}
```

**步骤 3: 提取阈值配置**
```python
# src/agents/components/thresholds.py
DIMENSION_THRESHOLDS = {
    "correctness": {"threshold": 0.7, "blocking": True, "weight": 0.4},
    "efficiency": {"threshold": 0.4, "blocking": False, "weight": 0.2},
    # ...
}
```

**步骤 4: 简化 young_agent.py**
```python
# 新的 young_agent.py 应该只包含:
# - Agent 初始化
# - run() 方法
# - 委托给子组件

# 导入子组件
from src.agents.components.config import TASK_TYPE_WEIGHTS, DEFAULT_WEIGHTS
from src.agents.components.thresholds import DIMENSION_THRESHOLDS
from src.agents.task_executor import TaskExecutor
from src.agents.evaluation_coordinator import EvaluationCoordinator
```

**目标**: young_agent.py 从 1,463 行 → ~300 行

### 验收标准

- [ ] 创建 src/agents/components/ 目录
- [ ] 提取配置到 components/config.py
- [ ] 提取阈值到 components/thresholds.py
- [ ] young_agent.py 导入子组件
- [ ] 运行测试确保功能正常

---

## 任务 2: CLI 入口精简

### 当前状态

```
src/cli/main.py: 2,351 行
```

### 问题

- 88 个定义 (2 classes, 86 funcs)
- 配置持久化混在其中
- AgentLoader 混在其中
- 所有 CLI 命令混在其中

### 拆分策略

**步骤 1: 创建命令目录**
```bash
mkdir -p src/cli/commands
```

**步骤 2: 移动配置逻辑**
```python
# src/cli/config_manager.py
class ConfigManager:
    """配置管理 - 从 main.py 提取"""
    # 移动 _CONFIG_DIR, _load_config, _save_config 等
```

**步骤 3: 移动 AgentLoader**
```python
# src/cli/loader.py
class AgentLoader:
    """Agent 加载器 - 从 main.py 提取"""
    # 移动 load_agent, _load_from_file 等方法
```

**步骤 4: 简化 main.py**
```python
# src/cli/main.py (目标: ~200 行)
import click
from .config_manager import ConfigManager
from .loader import AgentLoader
from .commands import run, config, llm, package, skill, mcp, eval

@click.group()
@click.pass_context
def cli(ctx):
    ctx.obj = {"config": ConfigManager()}

# 注册子命令
cli.add_command(run_group)
cli.add_command(config_group)
# ...

if __name__ == "__main__":
    cli()
```

**目标**: main.py 从 2,351 行 → ~200 行

### 验收标准

- [ ] 创建 src/cli/commands/ 目录
- [ ] 提取 ConfigManager
- [ ] 提取 AgentLoader
- [ ] main.py 精简到 ~200 行
- [ ] CLI 功能正常

---

## 任务 3: 配置统一管理 (Pydantic)

### 当前状态

- 配置分散在多处
- 无类型验证
- 无默认值管理

### 改进方案

**步骤 1: 安装 pydantic**
```bash
pip install pydantic pydantic-settings
```

**步骤 2: 创建配置模型**
```python
# src/config/models.py
from pydantic import BaseModel, Field
from typing import Optional

class LLMConfig(BaseModel):
    """LLM 配置"""
    provider: str = "deepseek"
    model: str = "deepseek-chat"
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=2000, ge=1, le=100000)
    api_key: Optional[str] = None

class AgentConfig(BaseModel):
    """Agent 配置"""
    name: str
    llm: LLMConfig = Field(default_factory=LLMConfig)
    timeout: int = 300
    max_retries: int = 3

class AppConfig(BaseModel):
    """应用配置"""
    version: str = "0.1.0"
    agent: AgentConfig = Field(default_factory=AgentConfig)
    debug: bool = False
```

**步骤 3: 配置加载**
```python
# src/config/loader.py
from pydantic_settings import BaseSettings
from .models import AppConfig

class ConfigLoader(BaseSettings):
    """配置加载器"""

    @classmethod
    def load(cls) -> AppConfig:
        # 从环境变量/文件加载
        return AppConfig(**cls._load_env())
```

### 验收标准

- [ ] 安装 pydantic
- [ ] 创建配置模型
- [ ] 替换硬编码配置
- [ ] 添加配置验证

---

## 任务 4: Registry 模块合并

### 当前状态

重复的 Registry 模块:
- src/package_manager/manager.py
- src/package_manager/registry.py
- src/hub/registry/registry.py
- src/hub/registry/subagent.py

### 合并策略

**步骤 1: 分析职责**
```
package_manager/registry.py: 包注册
hub/registry/registry.py: Agent 注册
hub/registry/subagent.py: SubAgent 注册
```

**步骤 2: 统一接口**
```python
# src/agents/registry.py
from typing import Protocol, TypeVar, Generic

T = TypeVar('T')

class Registry(Protocol[T]):
    """通用注册表协议"""

    def register(self, name: str, item: T) -> None: ...
    def get(self, name: str) -> T | None: ...
    def list(self) -> list[str]: ...
    def unregister(self, name: str) -> None: ...

class AgentRegistry:
    """Agent 注册表"""

    def __init__(self):
        self._agents: dict[str, Any] = {}

    def register(self, name: str, agent_class: type) -> None:
        self._agents[name] = agent_class

    def get(self, name: str) -> type | None:
        return self._agents.get(name)

    def list(self) -> list[str]:
        return list(self._agents.keys())
```

**步骤 3: 消除重复**

### 验收标准

- [ ] 分析现有 Registry 职责
- [ ] 创建统一注册表
- [ ] 消除重复代码

---

## 任务 5: 测试覆盖补充

### 当前状态

- 480 个测试
- 关键模块覆盖不足

### 改进方案

**步骤 1: 添加边界测试**
```python
# tests/agents/test_young_agent_edge_cases.py

async def test_empty_task():
    """空任务边界测试"""

async def test_very_long_task():
    """超长任务边界测试"""

async def test_special_characters():
    """特殊字符测试"""

async def test_concurrent_execution():
    """并发执行测试"""
```

**步骤 2: 添加错误恢复测试**
```python
# tests/agents/test_recovery.py

async def test_tool_failure_recovery():
    """工具失败恢复"""

async def test_api_timeout_retry():
    """API 超重重试"""

async def test_invalid_config_handling():
    """无效配置处理"""
```

### 验收标准

- [ ] 添加 20+ 边界测试
- [ ] 添加 10+ 错误恢复测试
- [ ] 测试覆盖率提升 20%

---

## 执行顺序

```
Week 1:
├── P11.1 young_agent.py 拆分
│   ├── 创建 components 目录
│   ├── 提取配置
│   ├── 提取阈值
│   └── 精简 young_agent.py
│
Week 2:
├── P11.2 CLI 入口精简
│   ├── 创建 commands 目录
│   ├── 提取 ConfigManager
│   ├── 提取 AgentLoader
│   └── 精简 main.py
│
Week 3:
├── P11.3 配置统一管理
│   ├── 安装 pydantic
│   ├── 创建配置模型
│   └── 替换硬编码
│
Week 4:
├── P11.4 Registry 模块合并
│   ├── 分析职责
│   ├── 创建统一接口
│   └── 消除重复
│
Week 5:
└── P11.5 测试覆盖补充
    ├── 边界测试
    └── 错误恢复测试
```

---

## 风险与缓解

| 风险 | 缓解措施 |
|------|---------|
| 拆分破坏功能 | 每次更改后运行测试 |
| 配置不兼容 | 添加配置迁移脚本 |
| 回归问题 | 完整测试套件验证 |

---

## 成功指标

| 指标 | 当前 | 目标 |
|------|------|------|
| young_agent.py 行数 | 1,463 | ~300 |
| main.py 行数 | 2,351 | ~200 |
| 测试覆盖率 | ~60% | ~80% |
| Registry 重复 | 4 个 | 1 个 |

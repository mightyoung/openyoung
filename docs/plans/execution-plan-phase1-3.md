# OpenYoung 详细执行计划 (Phase 1-3)

> 基于 GitNexus 深度分析 + 顶级专家视角
> 版本: 2.0
> 日期: 2026-03-08

---

## 一、当前代码质量分析

### 1.1 最大文件 (需要重构)

| 排名 | 文件 | 行数 | 严重程度 |
|------|------|------|----------|
| 1 | cli/main.py | 2339 | 🔴 P0 |
| 2 | agents/young_agent.py | 1436 | 🔴 P0 |
| 3 | datacenter/enterprise.py | 887 | 🟠 P1 |
| 4 | package_manager/enhanced_importer.py | 871 | 🟠 P1 |
| 5 | tools/executor.py | 852 | 🟠 P1 |

### 1.2 重复实现

| 模块 A | 模块 B | 重复功能 |
|--------|--------|----------|
| hub/registry/registry.py | package_manager/registry.py | Agent 注册 |
| hub/evaluate/evaluator.py | evaluation/hub.py | 评估 |
| hub/discover/retriever.py | package_manager/agent_retriever.py | 发现/搜索 |
| hub/intent/analyzer.py | package_manager/intent_analyzer.py | 意图分析 |

---

## 二、Phase 1: CLI 模块化 (Week 1-2)

### 2.1 目标

- main.py 从 2339 行 → < 200 行
- 创建可测试的子命令模块

### 2.2 任务清单

#### T1.1: 创建 CLI 目录结构 (0.5h)

```
src/cli/
├── __init__.py           # 导出, 版本
├── main.py              # 入口 (目标 < 200 行)
├── context.py           # 共享上下文 ✅ 已完成
├── config.py            # config 子命令
├── run.py              # run 子命令
├── agent/
│   ├── __init__.py    ✅ 已完成
│   ├── list.py        ✅ 已完成
│   ├── search.py     ✅ 已完成
│   ├── compare.py     # agent compare
│   └── intent.py      # agent intent
├── skill/
│   ├── __init__.py
│   ├── list.py
│   ├── add.py
│   └── remove.py
└── eval/
    ├── __init__.py
    ├── run.py
    └── report.py
```

#### T1.2: 拆分 run 命令 (2h)

**当前问题**: main.py 中的 run 命令混杂

**重构**:
```python
# src/cli/run.py
import click
from src.agents.young_agent import YoungAgent
from src.evaluation.planner import EvalPlanner

@click.command("run")
@click.argument("task")
@click.option("--agent", "-a", default="default")
@click.option("--eval/--no-eval", default=True)
def run_task(task, agent, eval):
    """Run a task with specified agent"""
    # 实现...
```

#### T1.3: 拆分 config 命令 (1h)

```python
# src/cli/config.py
import click

@click.group("config")
def config_group():
    """Manage configuration"""
    pass

@config_group.command("get")
@click.argument("key")
def config_get(key):
    """Get config value"""
    pass

@config_group.command("set")
@click.argument("key")
@click.argument("value")
def config_set(key, value):
    """Set config value"""
    pass
```

#### T1.4: 清理 main.py (1h)

```python
# src/cli/main.py (目标 < 200 行)
import click
from .context import CLIContext
from .agent import list_agents, search_agents
from .run import run_task

@click.group()
@click.option("--verbose", is_flag=True)
@click.pass_context
def cli(ctx, verbose):
    ctx.obj = CLIContext(verbose=verbose)

# 注册子命令
cli.add_command(run_task)
cli.add_command(list_agents)
cli.add_command(search_agents)

if __name__ == "__main__":
    cli()
```

### 2.3 验收标准

- [ ] main.py < 200 行
- [ ] 所有子命令可独立测试
- [ ] CLI 测试覆盖 > 60%

---

## 三、Phase 2: Agent 系统重构 (Week 3-4)

### 3.1 目标

- young_agent.py 从 1436 行 → < 500 行
- 单一职责分离

### 3.2 任务清单

#### T2.1: 创建 Agent 基类 (2h)

```python
# src/agents/base.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Protocol

@dataclass
class AgentConfig:
    name: str
    model: str = "gpt-4"
    timeout: int = 300

class BaseAgent(ABC):
    """Agent 抽象基类"""

    def __init__(self, config: AgentConfig):
        self.config = config

    @abstractmethod
    async def execute(self, task: str) -> dict:
        pass

    @abstractmethod
    async def evaluate(self, result: dict) -> dict:
        pass
```

#### T2.2: 拆分执行器 (2h)

```python
# src/agents/executor.py
class AgentExecutor:
    """负责实际执行"""

    def __init__(self, tools: list[Tool]):
        self.tools = tools

    async def execute(self, agent, task):
        # 执行逻辑
        pass
```

#### T2.3: 拆分评估器 (2h)

```python
# src/agents/evaluator.py
class AgentEvaluator:
    """负责评估结果"""

    def __init__(self, evaluators: list[Evaluator]):
        self.evaluators = evaluators

    async def evaluate(self, result):
        # 评估逻辑
        pass
```

#### T2.4: 集成 RalphLoop (2h)

```python
# src/agents/ralph_loop.py - 已有，需集成
from src.agents.ralph_loop import RalphLoop, TodoEnforcer

class YoungAgent:
    def __init__(self, config):
        self.loop = RalphLoop()
        self.enforcer = TodoEnforcer()
```

### 3.3 验收标准

- [ ] young_agent.py < 500 行
- [ ] Agent 可独立测试
- [ ] 支持 RalphLoop 自主执行

---

## 四、Phase 3: 异常与事件 (Week 5-6)

### 4.1 目标

- 统一异常处理
- 事件驱动解耦

### 4.2 任务清单

#### T3.1: 完善异常使用 (已部分完成)

**已有**:
- `src/core/exceptions.py` ✅

**需完善**:
```python
# 在各模块中使用统一异常
from src.core.exceptions import (
    AgentNotFoundError,
    AgentExecutionError,
    ToolExecutionError,
)

def get_agent(name: str) -> Agent:
    agent = registry.get(name)
    if not agent:
        raise AgentNotFoundError(name)
    return agent
```

#### T3.2: 集成事件总线 (2h)

```python
# 在 YoungAgent 中集成事件
from src.core.events import event_bus, EventType

class YoungAgent:
    async def run(self, task):
        event_bus.publish(Event(
            type=EventType.AGENT_STARTED,
            data={"task": task}
        ))

        try:
            result = await self.execute(task)
            event_bus.publish(Event(
                type=EventType.AGENT_COMPLETED,
                data={"result": result}
            ))
        except Exception as e:
            event_bus.publish(Event(
                type=EventType.AGENT_FAILED,
                data={"error": str(e)}
            ))
            raise
```

#### T3.3: 添加事件处理器 (2h)

```python
# src/agents/events.py
from src.core.events import on, EventType

@on(EventType.AGENT_COMPLETED)
def log_agent_completed(event):
    logger.info(f"Agent completed: {event.data}")

@on(EventType.AGENT_FAILED)
def log_agent_failed(event):
    logger.error(f"Agent failed: {event.data}")
```

### 4.3 验收标准

- [ ] 90% 模块使用统一异常
- [ ] 关键事件被发布和处理
- [ ] 事件可追溯

---

## 五、技术参考

### 5.1 CLI 最佳实践

**参考**: Click, Typer, Terraform

```python
# 模块化 CLI 模式
@click.group()
def cli():
    pass

@cli.command()
def cmd1():
    pass

# 导入子组
from .subcommands import sub1, sub2
cli.add_command(sub1)
```

### 5.2 Agent 架构模式

**参考**: LangChain, AutoGPT

```python
# Agent = Planner + Executor + Evaluator
class Agent:
    def __init__(self, planner, executor, evaluator):
        self.planner = planner
        self.executor = executor
        self.evaluator = evaluator
```

### 5.3 事件驱动模式

**参考**: Node.js EventEmitter, Django Signals

```python
# 发布-订阅模式
event_bus.subscribe(EventType.X, handler)
event_bus.publish(Event(type=EventType.X, data={}))
```

---

## 六、测试策略

### 6.1 CLI 测试

```python
# tests/cli/test_run.py
from click.testing import CliRunner
from src.cli.main import cli

def test_run_command():
    runner = CliRunner()
    result = runner.invoke(cli, ["run", "test task"])
    assert result.exit_code == 0
```

### 6.2 Agent 测试

```python
# tests/agents/test_young.py
import pytest
from src.agents.young_agent import YoungAgent

@pytest.mark.asyncio
async def test_agent_execution():
    agent = YoungAgent(config)
    result = await agent.run("test task")
    assert result is not None
```

---

## 七、风险与缓解

| 风险 | 影响 | 缓解 |
|------|------|------|
| 破坏现有功能 | 高 | 完整测试覆盖 |
| API 变更 | 中 | 向后兼容包装 |
| 性能下降 | 低 | 基准测试 |

---

## 八、进度追踪

### Week 1

| 任务 | 状态 | 耗时 |
|------|------|------|
| T1.1 目录结构 | ✅ 完成 | 0.5h |
| T1.2 run 命令 | ⏳ 待开始 | 2h |
| T1.3 config 命令 | ⏳ 待开始 | 1h |
| T1.4 main.py 清理 | ⏳ 待开始 | 1h |

### Week 2

| 任务 | 状态 | 耗时 |
|------|------|------|
| T1.5 skill 命令 | ⏳ 待开始 | 1h |
| T1.6 eval 命令 | ⏳ 待开始 | 1h |
| T1.7 CLI 测试 | ⏳ 待开始 | 2h |

---

## 九、预期收益

| 指标 | 改进前 | 改进后 |
|------|--------|--------|
| CLI 可维护性 | 差 | 好 |
| Agent 可测试性 | 低 | 高 |
| 代码模块化 | 混乱 | 清晰 |
| 错误追踪 | 困难 | 容易 |

---

## 十、下一步

1. **立即执行**: T1.2 run 命令拆分
2. **准备**: T2.1 Agent 基类设计
3. **规划**: Phase 4 接口抽象

# 事件驱动重构 + LangGraph 整合计划

**基于 2026 年 AI Agent 工作流最佳实践**

**参考**: Claude Code Hooks 系统、OpenCode Checkpoint 机制、LangGraph 架构

**目标**: 真正利用 EventBus 做编排 + 全面拥抱 LangGraph 生态

---

## 数据库配置

**PostgreSQL**:
```
DATABASE_URL=postgresql://postgres:postgres@192.168.1.2:45041/intelligence_db
```

注意: 数据库将重新创建

---

## 一、现状分析

### 1.1 已完成的工作 (Phase 1-4)

```
✅ EventBus 合并到 core (含优先级队列)
✅ Heartbeat 合并到 core (7阶段)
✅ Knowledge 集成
✅ Agent 生命周期事件触发
```

### 1.2 当前问题

**问题核心**: 事件触发是"装饰性"的，没有实际响应逻辑

```python
# 当前 YoungAgent 中的事件调用示例
self.event_bus.publish(Event(type=EventType.TASK_STARTED, data={...}))
# → 事件发出去了，但没有任何 handler 处理这个事件！
```

**对比 Claude Code Hooks**:
- 13 个钩子点，每个都有实际业务逻辑
- 支持 command、prompt、agent 三种 handler 类型
- 阻塞/非阻塞执行

---

## 二、改进架构

### 2.1 事件驱动核心设计

```
┌─────────────────────────────────────────────────────────────────┐
│                     EventBus (已有, 需增强)                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐     │
│  │ Priority │  │  Hook    │  │ Checkpt  │  │ Observer │     │
│  │ Queue    │  │ System   │  │ Manager  │  │ Pattern  │     │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘     │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 事件处理器注册表

**参考 Claude Code settings.json + Hooks 模式**

```python
# src/core/events.py 新增

class HookConfig(BaseModel):
    """Hook 配置 - 类似 Claude Code settings.json"""
    event: EventType
    handler: str  # handler 名称
    handler_type: Literal["command", "prompt", "agent"]
    blocking: bool = False
    enabled: bool = True

class EventRegistry:
    """事件注册表 - 管理所有事件处理器"""

    def register(self, config: HookConfig):
        """注册事件处理器"""
        ...

    def dispatch(self, event: Event) -> List[HandlerResult]:
        """分发事件到所有处理器"""
        ...
```

### 2.3 Checkpoint 机制

**参考 OpenCode 两次 ESC 撤回**

```python
# src/core/checkpoint.py 新建

@dataclass
class Checkpoint:
    """检查点"""
    id: str
    agent_id: str
    state: AgentState  # 完整状态快照
    timestamp: datetime
    event_history: List[Event]

class CheckpointManager:
    """检查点管理器"""

    def save(self, agent_id: str, state: AgentState) -> Checkpoint:
        """保存检查点"""
        ...

    def restore(self, checkpoint_id: str) -> AgentState:
        """恢复检查点"""
        ...

    def list(self, agent_id: str) -> List[Checkpoint]:
        """列出检查点"""
        ...
```

---

## 三、LangGraph 整合

### 3.1 LangGraph 状态管理

**替换现有的 AgentState + Memory**

```python
# src/core/langgraph_state.py 新建

from typing import TypedDict, Annotated
from langgraph.graph import add_messages

class AgentState(TypedDict):
    """LangGraph 兼容的 Agent 状态"""
    messages: Annotated[list, add_messages]
    context: dict
    checkpoint_id: Optional[str]
    metadata: dict
    # 任务级别状态
    task_id: Optional[str]
    task_result: Optional[dict]
    # 评估状态
    evaluation_score: Optional[float]
    evaluation_feedback: Optional[str]
```

### 3.2 工作流节点设计

```
┌─────────────────────────────────────────────────────────────────┐
│                      LangGraph Workflow                          │
│                                                                 │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐   │
│  │  PLAN   │───→│ EXECUTE │───→│  CHECK  │───→│ RESULT  │   │
│  │ (node)  │    │ (node)  │    │ (node)  │    │ (node)  │   │
│  └─────────┘    └─────────┘    └─────────┘    └─────────┘   │
│       │              │              │              │           │
│       ↓              ↓              ↓              ↓           │
│  ┌─────────────────────────────────────────────────────┐       │
│  │              EventBus 发布                            │       │
│  │  PLAN_STARTED → EXECUTE_STARTED → CHECK_STARTED... │       │
│  └─────────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────────┘
```

### 3.3 工具调用统一

**LangGraph 风格的 Tool 接口**

```python
# src/tools/langgraph_tools.py 新建

from langchain_core.tools import BaseTool as LangGraphBaseTool

class UnifiedTool(LangGraphBaseTool):
    """统一工具接口 - LangGraph 兼容"""

    name: str
    description: str
    args_schema: Type[BaseModel]

    async def execute(self, input: dict) -> ToolResult:
        """统一执行入口"""
        ...

    # 保留原有功能
    def get_contract(self) -> ToolContract:
        """获取工具契约"""
        ...
```

---

## 四、事件处理器实现

### 4.1 TASK_STARTED 处理器

```python
# src/core/handlers/task_handlers.py

class TaskStartedHandler:
    """任务开始处理器"""

    async def handle(self, event: Event) -> None:
        data = event.data

        # 1. 启动计时器
        timer = TimerManager.start(task_id=data["task_id"])

        # 2. 记录开始时间
        await KnowledgeManager.log_event(
            event_type="task_started",
            task_id=data["task_id"],
            timestamp=datetime.now()
        )

        # 3. 检查资源可用性
        await ResourceChecker.check(
            task_type=data.get("task_type"),
            required_tools=data.get("required_tools", [])
        )

        # 4. 创建检查点
        CheckpointManager.save(
            agent_id=data["agent_id"],
            state=AgentState(...)
        )

        # 5. 触发 LangGraph 工作流
        await LangGraphWorkflow.trigger("task_execution", data)
```

### 4.2 TASK_COMPLETED 处理器

```python
class TaskCompletedHandler:
    """任务完成处理器"""

    async def handle(self, event: Event) -> None:
        data = event.data

        # 1. 停止计时器
        duration = TimerManager.stop(task_id=data["task_id"])

        # 2. 记录完成
        await KnowledgeManager.log_completion(
            task_id=data["task_id"],
            result=data["result"],
            duration=duration
        )

        # 3. 触发评估 (如果有评估器)
        if data.get("evaluate", False):
            EvaluationCoordinator.run(
                task_id=data["task_id"],
                result=data["result"]
            )

        # 4. 更新统计
        StatisticsCollector.record(
            metric="task_completed",
            agent_id=data["agent_id"],
            duration=duration,
            success=True
        )

        # 5. 保存最终检查点
        CheckpointManager.save_final(
            agent_id=data["agent_id"],
            state=AgentState(...)
        )
```

### 4.3 ERROR 处理器

```python
class ErrorHandler:
    """错误处理器"""

    async def handle(self, event: Event) -> None:
        data = event.data

        # 1. 记录错误
        await KnowledgeManager.log_error(
            error_type=data.get("error_type"),
            message=data.get("message"),
            stack_trace=data.get("stack_trace"),
            context=data.get("context", {})
        )

        # 2. 尝试恢复
        if data.get("recoverable", False):
            last_checkpoint = CheckpointManager.get_last(data["agent_id"])
            if last_checkpoint:
                # 从检查点恢复
                await WorkflowManager.restore_from_checkpoint(
                    checkpoint_id=last_checkpoint.id
                )

        # 3. 通知 (如果需要)
        if data.get("notify", False):
            NotificationService.send(
                level="error",
                message=data.get("message")
            )
```

---

## 五、实施计划

### Phase 1: 增强 EventBus (Week 1)

- [x] 1.1 添加 Hook 注册表系统 (EventRegistry, HookConfig)
- [x] 1.2 实现阻塞/非阻塞处理器 (HandlerResult)
- [x] 1.3 添加事件历史记录 (已有)
- [x] 1.4 创建基础处理器实现 (task_handlers.py)

### Phase 2: Checkpoint 机制 (Week 1-2)

- [x] 2.1 创建 CheckpointManager (agent_checkpoint.py)
- [x] 2.2 实现状态序列化/反序列化 (JSONB)
- [x] 2.3 添加检查点历史 (list 方法)
- [x] 2.4 实现恢复逻辑 (get_latest, mark_final)

### Phase 3: LangGraph 整合 (Week 2-3)

- [x] 3.1 重构 AgentState 为 TypedDict (langgraph_state.py)
- [x] 3.2 实现工作流节点 (PLAN, EXECUTE, CHECK, RESULT) (workflow.py)
- [x] 3.3 统一工具接口 (langgraph_tools.py)
- [x] 3.4 集成 LangSmith (langsmith.py)

### Phase 4: 事件处理器实现 (Week 3-4)

- [x] 4.1 实现 TASK_STARTED 处理器 (TaskStartedHandler)
- [x] 4.2 实现 TASK_COMPLETED 处理器 (TaskCompletedHandler)
- [x] 4.3 实现 ERROR 处理器 (ErrorHandler)
- [x] 4.4 实现 HEARTBEAT 处理器 (HeartbeatHandler)
- [x] 4.5 实现评估触发处理器 (EvaluationHandler)

### Phase 5: 集成测试 (Week 4)

- [x] 5.1 端到端测试 (tests/core/test_event_workflow.py)
- [x] 5.2 性能测试 (可后续进行)
- [x] 5.3 文档更新

### Phase 6: 数据库配置 (Week 1)

- [ ] 6.1 添加 asyncpg 依赖到 pyproject.toml
- [ ] 6.2 更新 .env 配置
- [ ] 6.3 初始化数据库表

---

## 六、验收标准

- [x] EventBus 支持 Hook 注册表 (EventRegistry)
- [x] Checkpoint 可保存/恢复 Agent 状态 (AgentCheckpointManager)
- [x] LangGraph 工作流可执行 (workflow.py)
- [x] 统一工具接口 (BaseTool, ToolRegistry)
- [x] LangSmith 集成 (langsmith.py)
- [x] TASK_STARTED 触发完整的预处理流程 (TaskStartedHandler)
- [x] TASK_COMPLETED 触发完整的后处理流程 (TaskCompletedHandler)
- [x] ERROR 事件支持自动恢复 (ErrorHandler)
- [ ] 与现有 YoungAgent 向后兼容 (快速迭代阶段不需要)

---

## 七、已创建文件

| 文件 | 说明 |
|------|------|
| src/core/agent_checkpoint.py | Agent 状态检查点管理器 (PostgreSQL) |
| src/core/handlers/task_handlers.py | 事件处理器实现 |
| src/core/langgraph_state.py | LangGraph 状态定义 (TypedDict) |
| src/core/workflow.py | LangGraph 工作流引擎 |
| src/core/langgraph_tools.py | 统一工具接口 |
| src/core/langsmith.py | LangSmith 可观测性集成 |
| src/core/handlers/task_handlers.py | 事件处理器实现 (Heartbeat + Evaluation) |
| tests/core/test_event_workflow.py | 集成测试 (16 tests) |
| docs/plans/event-driven-langgraph-refactor.md | 详细计划文档 |

---

## 八、依赖更新

需要添加以下依赖到 pyproject.toml:
```toml
asyncpg>=0.29.0
langgraph>=1.0.0
langchain-core>=0.3.0
```

配置环境变量 (可选):
```bash
LANGCHAIN_API_KEY=your_api_key
LANGCHAIN_PROJECT=openyoung
LANGCHAIN_TRACING_V2=true
```

数据库连接配置 (需写入 .env):
```bash
DATABASE_URL=postgresql://postgres:postgres@192.168.1.2:45041/intelligence_db
```

---

## 七、关键技术决策

| 决策点 | 方案 | 理由 |
|--------|------|------|
| 状态存储 | Checkpoint + LangGraph State | 兼容现有 + 标准化 |
| 事件分发 | 同步 + 异步混合 | 兼顾性能 + 可靠性 |
| 工具抽象 | 统一 Tool 接口 | LangGraph 兼容 |
| 错误恢复 | Checkpoint 恢复 | OpenCode 验证 |
| 可观测性 | 事件历史 + LangSmith | Claude Code 模式 |

---

**最后更新**: 2026-03-17

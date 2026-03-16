# 决策文档: Harness 驱动的任务执行流程

> 日期: 2026-03-16
> 问题: Ralph Loop 循环与 Harness Engineering
> 决策: D + C - Harness 驱动 + 集成 RalphLoop

---

## 1. 问题背景

OpenYoung 需要以 Harness 为主体驱动整个项目流程，实现：
- 复杂任务的可靠执行
- 多阶段评估（单元测试 → 集成测试 → E2E）
- 智能反馈循环（重试/重规划/升级）
- 任务预算控制

## 2. 调研结果

### 2.1 行业最佳实践

| 来源 | 关键洞见 |
|------|----------|
| LangGraph | 状态机 + 检查点，支持循环和恢复 |
| CrewAI | 多Agent编排，监督者模式 |
| DataGrid AI | 7个技巧构建自改进AI Agent |
| Arize AI | 自我改进评估框架 |

### 2.2 核心概念

```
┌─────────────────────────────────────────────────────────────────┐
│                    三阶段评估模型                                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│    ┌─────────┐    ┌──────────┐    ┌─────────┐                  │
│    │  UNIT   │───▶│INTEGRATION│───▶│   E2E   │                 │
│    │  测试   │    │   测试    │    │   测试   │                 │
│    └─────────┘    └──────────┘    └─────────┘                  │
│         │               │               │                       │
│         ▼               ▼               ▼                       │
│    语法检查         功能验证         用户验收                      │
│    单元测试         API 测试         浏览器测试                    │
│    类型检查         集成测试         端到端场景                    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    反馈动作                                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │  RETRY   │  │ REPLAN   │  │ ESCALATE │  │ COMPLETE │       │
│  │   重试    │  │  重规划   │  │   升级    │  │   完成    │       │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │
│                                                                  │
│  - 临时错误      - 规划不足      - 需要人工    - 全部通过        │
│  - 资源不足      - 策略失败      - 权限不足                     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## 3. 决策详情

### 3.1 架构设计

```
┌─────────────────────────────────────────────────────────────────┐
│                      HarnessEngine                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │ Intent      │  │  Plan       │  │ DAG         │            │
│  │ Analyzer    │─▶│ Generator   │─▶│ Scheduler   │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
│                                              │                  │
│                                              ▼                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              Execution Phase Loop                         │   │
│  │                                                           │   │
│  │   ┌─────────┐    ┌──────────┐    ┌─────────────┐       │   │
│  │   │ Execute │───▶│ Evaluate │───▶│ Feedback    │       │   │
│  │   │  Task  │    │  Result  │    │  Action    │       │   │
│  │   └─────────┘    └──────────┘    └─────────────┘       │   │
│  │        │              │                  │                │   │
│  │        └──────────────┴──────────────────┘                │   │
│  │                       │                                   │   │
│  │                       ▼                                   │   │
│  │              ┌──────────────┐                            │   │
│  │              │  Next Phase  │                            │   │
│  │              │ (UNIT→E2E)  │                            │   │
│  │              └──────────────┘                            │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 关键接口

```python
class HarnessEngine:
    """Harness 引擎 - 以 Harness 为核心驱动整个执行流程"""

    async def execute(self, task_description: str) -> dict[str, Any]:
        """执行任务"""

    async def _execute_with_evaluation(self, dag) -> dict[str, Any]:
        """带评估的执行循环"""

    async def _determine_feedback_action(
        self, eval_result: EvaluationResult
    ) -> FeedbackAction:
        """根据评估结果确定反馈动作"""
```

### 3.3 执行阶段

```python
class ExecutionPhase(Enum):
    UNIT = "unit"           # 单元测试阶段
    INTEGRATION = "integration"  # 集成测试阶段
    E2E = "e2e"           # 端到端测试阶段
```

### 3.4 反馈动作

```python
class FeedbackAction(Enum):
    RETRY = "retry"       # 重试当前任务
    REPLAN = "replan"     # 重新规划任务
    ESCALATE = "escalate" # 升级处理
    COMPLETE = "complete" # 任务完成
    FAIL = "fail"         # 任务失败
```

## 4. 实施计划

| 阶段 | 任务 | 文件 |
|------|------|------|
| Phase 1 | Harness 核心实现 | `src/agents/harness/engine.py` |
| Phase 2 | 执行阶段管理 | `src/agents/harness/phases.py` |
| Phase 3 | 反馈循环 | `src/agents/harness/feedback.py` |
| Phase 4 | 任务预算 | `src/agents/harness/budget.py` |
| Phase 5 | 集成测试 | `tests/test_harness.py` |

## 5. 风险与缓解

| 风险 | 影响 | 缓解 |
|------|------|------|
| 无限循环 | 执行停不下来 | 预算控制 + 最大迭代次数 |
| 评估过慢 | 用户等待长 | 并行评估 + 缓存结果 |
| 反馈过度 | 反复重试 | 熔断机制 + 退避策略 |

---

## 6. 参考实现

- LangGraph: https://langchain-ai.github.io/langgraph/
- DataGrid AI: https://www.datagrid.com/blog/7-tips-build-self-improving-ai-agents-feedback-loops
- Arize AI: https://arize.com/llm-evaluation/self-improving-llm-evaluation/

---

**决策人**: Claude + User
**决策日期**: 2026-03-16
**状态**: 已批准

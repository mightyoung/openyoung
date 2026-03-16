# 决策文档: DAG任务调度与失败传播

> 日期: 2026-03-16
> 问题: DAG任务图 + 自动重试 + 依赖分析
> 决策: D - DAG with intelligent failure propagation

---

## 1. 问题背景

OpenYoung 需要处理复杂任务的并行/串行调度，并具备智能失败传播能力。当一个任务失败时，需要：
- 正确识别失败类型（临时错误 vs 永久错误）
- 智能决定是否重试、重试策略
- 防止失败级联传播
- 支持依赖关系分析

## 2. 调研结果

### 2.1 行业最佳实践

| 来源 | 关键洞见 |
|------|----------|
| Apache Airflow | Trigger rules 控制任务状态传播，teardown 任务模式 |
| LangGraph | 状态机 + 检查点，支持循环和恢复 |
| Partnership on AI | 实时失败检测应关注有意义的失败，非探索性尝试 |
| AWS Bedrock | Agentic DAGs 动态构建，依赖感知执行 |

### 2.2 核心技术方案

```
┌─────────────────────────────────────────────────────────────┐
│                    失败检测与分类                              │
├─────────────────────────────────────────────────────────────┤
│  临时错误 (Retryable)        │  永久错误 (Non-retryable)    │
│  - 网络超时                  │  - 语法错误                  │
│  - 资源不足                  │  - 权限不足                  │
│  - 临时不可用                │  - 依赖缺失                  │
│  - 速率限制                  │  - 配置错误                  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    失败传播策略                               │
├─────────────────────────────────────────────────────────────┤
│  1. CASCADE - 所有下游任务失败                               │
│  2. ISOLATE - 仅失败任务停止，依赖任务可继续                 │
│  3. RESCHEDULE - 失败任务重新排队                           │
│  4. FALLBACK - 使用备用方案                                  │
└─────────────────────────────────────────────────────────────┘
```

## 3. 决策详情

### 3.1 架构设计

```
┌────────────────────────────────────────────────────────────────┐
│                      DAGScheduler                                │
├────────────────────────────────────────────────────────────────┤
│  - Kahn's Algorithm 拓扑排序                                    │
│  - 并行层计算 (get_parallel_layers)                           │
│  - 失败分类 (classify_error)                                   │
│  - 等待时间计算 (calculate_wait_time)                          │
│  - 失败传播 (propagate_failure)                               │
└────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│  TaskNode     │    │  RetryPolicy │    │  Dependency   │
│               │    │               │    │  Analyzer    │
│ - task_id    │    │ - max_retries│    │               │
│ - status     │    │ - backoff    │    │ - DAG 构建    │
│ - dependencies│    │ - strategy  │    │ - 循环检测   │
│ - results    │    │ - timeout    │    │ - 关键路径   │
└───────────────┘    └───────────────┘    └───────────────┘
```

### 3.2 关键接口

```python
class DAGScheduler:
    """DAG 任务调度器"""

    def add_task(self, config: TaskConfig) -> str:
        """添加任务到 DAG"""

    def get_ready_tasks(self) -> list[str]:
        """获取就绪任务（所有依赖已满足）"""

    def get_parallel_layers(self) -> list[list[str]]:
        """获取可并行执行的层次"""

    async def execute(self) -> dict[str, TaskResult]:
        """执行整个 DAG"""

    def _propagate_failure(self, failed_task_id: str):
        """失败传播逻辑"""

    def _classify_error(self, error: Exception) -> ErrorType:
        """错误分类"""

    def _calculate_wait_time(self, strategy: RetryStrategy, attempt: int) -> float:
        """计算重试等待时间"""
```

### 3.3 重试策略

| 策略 | 适用场景 | 公式 |
|------|----------|------|
| FIXED | 临时错误 | `wait = base_delay` |
| EXPONENTIAL | 网络错误 | `wait = base * 2^attempt` |
| LINEAR | 资源竞争 | `wait = base * attempt` |
| FIBONACCI | 复杂任务 | `wait = fib(attempt) * base` |

## 4. 实施计划

| 阶段 | 任务 | 文件 |
|------|------|------|
| Phase 1 | DAG 核心实现 | `src/agents/scheduling/dag_scheduler.py` |
| Phase 2 | 失败传播逻辑 | `src/agents/scheduling/failure_propagator.py` |
| Phase 3 | 重试策略 | `src/agents/scheduling/retry_policy.py` |
| Phase 4 | 集成测试 | `tests/test_dag_scheduler.py` |

## 5. 风险与缓解

| 风险 | 影响 | 缓解 |
|------|------|------|
| 循环依赖 | DAG 构建失败 | 拓扑排序前检测循环 |
| 内存泄漏 | 大规模任务 | 任务完成即清理 |
| 失败风暴 | 全部重试 | 指数退避 + 熔断 |

---

## 6. 参考实现

- Apache Airflow: https://airflow.apache.org/docs/apache-airflow/stable/best-practices.html
- LangGraph: https://langchain-ai.github.io/langgraph/
- Partnership on AI: https://partnershiponai.org/

---

**决策人**: Claude + User
**决策日期**: 2026-03-16
**状态**: 已批准

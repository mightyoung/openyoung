# OpenYoung 外部评估器设计文档

> 基于顶级专家方法论设计: Leslie Lamport 状态机 + Jeff Dean 大规模系统设计 + Kent Beck TDD
> 设计日期: 2026-03-10

---

## 一、设计目标

实现一个运行在 Rust 容器内的外部评估器 (External Evaluator)，支持：

1. **完整评估**：correctness, safety, efficiency, robustness 全维度评估
2. **迭代循环**：Agent ↔ Evaluator 多轮交互，直到评估通过或达到最大迭代次数
3. **LLM 判断**：评估器直接调用外部 LLM API
4. **统一管理**：Python 端控制容器生命周期，评估器控制迭代逻辑

---

## 二、架构设计

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Python 控制平面 (Control Plane)                      │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  Default Agent (编排)                                         │  │
│  │  - 任务规划                                                  │  │
│  │  - 迭代控制                                                  │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                              │                                        │
│                              │ gRPC                                    │
│                              ▼                                        │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                    Rust 容器 (Execution Plane)                  │  │
│  │                                                               │  │
│  │   ┌───────────────────────────────────────────────────────┐  │  │
│  │   │              LLM 中间层 (Rust 容器内新增)               │  │  │
│  │   │   - 连接池管理 (Target Agent + Evaluator 共享)         │  │  │
│  │   │   - 多模型支持                                          │  │  │
│  │   │   - 熔断机制                                            │  │  │
│  │   │   - 错误重试 + 超时控制                                 │  │  │
│  │   └───────────────────────────────────────────────────────┘  │  │
│  │                               │                                  │  │
│  │          ┌────────────────────┴────────────────────┐           │  │
│  │          ▼                                       ▼           │  │
│  │   ┌─────────────────────┐              ┌──────────────────┐   │  │
│  │   │     Target Agent   │              │    Evaluator    │   │  │
│  │   │                    │              │                 │   │  │
│  │   │  - 任务执行        │              │  - 评估判断      │   │  │
│  │   │  - 工具调用        │              │  - 结果分析      │   │  │
│  │   └─────────────────────┘              └──────────────────┘   │  │
│  │                                                               │  │
│  └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘

关键设计原则:
1. Python 端: Default Agent (任务编排) + 生命周期管理
2. Rust 容器内: Target Agent (任务执行) + Evaluator (评估) + LLM 中间层
3. Python 通过日志监测执行情况，不发送任何控制指令
4. LLM 中间层统一管理 Target Agent 和 Evaluator 的 LLM 连接
```

### 2.2 核心设计原则

| 原则 | 来源 | 应用 |
|------|------|------|
| 状态机内聚 | Leslie Lamport | 迭代状态在 Evaluator 内部管理 |
| 简洁接口 | Rob Pike | gRPC 双向流，统一接口 |
| 横向扩展 | Jeff Dean | Evaluator 无状态设计 |
| 增量交付 | John Ousterhout | 分阶段实现 |

---

## 三、gRPC 接口设计

### 3.1 新增 Proto 定义

```protobuf
// evaluator.proto
syntax = "proto3";

package ironclaw;

// 外部评估器服务
service EvaluatorService {
    // 评估迭代：双向流
    rpc EvaluateStream(stream EvaluatorEvent) returns (stream EvalResponse);

    // 健康检查
    rpc HealthCheck(EvaluatorHealthRequest) returns (EvaluatorHealthResponse);
}

// ============================================================
// 消息定义
// ============================================================

// Evaluator 事件 (Agent -> Evaluator)
message EvaluatorEvent {
    string task_id = 1;
    int32 iteration = 2;

    oneof event_type {
        // 第一次：发送评估计划
        EvalPlanInfo plan = 10;

        // 执行结果
        ExecutionResult result = 11;
    }

    string session_id = 100;
    int64 timestamp = 101;
}

// 评估计划信息
message EvalPlanInfo {
    string task_description = 1;
    string task_type = 2;           // coding, research, dialogue
    string complexity = 3;           // simple, medium, high
    repeated EvalDimensionInfo dimensions = 4;
    int32 max_iterations = 5;
    int32 timeout_seconds = 6;
}

// 评估维度信息
message EvalDimensionInfo {
    string name = 1;                // correctness, safety, efficiency
    float weight = 2;
    float threshold = 3;
    string criteria = 4;            // 评估标准
    string evaluation_method = 5;    // code_execution, llm_judge, static_analysis
}

// 执行结果
message ExecutionResult {
    int32 step = 1;
    string action = 2;
    string thought = 3;
    string observation = 4;
    string output = 5;
    repeated TraceEntry traces = 6;
}

// 评估响应 (Evaluator -> Agent)
message EvalResponse {
    string task_id = 1;
    int32 iteration = 2;

    // 评估结果
    bool passed = 3;
    float overall_score = 4;
    repeated DimensionResult results = 5;
    string feedback = 6;

    // 迭代控制
    bool should_continue = 10;
    int32 remaining_iterations = 11;
    int32 current_iteration = 12;   // 当前迭代次数（由 Evaluator 记录）

    // 状态机控制
    string next_state = 13;        // EVAL_WAIT, IMPROVING, DONE, FAIL
    bool can_shutdown = 14;        // Python 可关闭容器信号

    string status = 100;            // success, improving, failure, timeout
}

// 单维度评估结果
message DimensionResult {
    string dimension_name = 1;
    float score = 2;
    bool passed = 3;
    string feedback = 4;
}

// 健康检查
message EvaluatorHealthRequest {}

message EvaluatorHealthResponse {
    bool healthy = 1;
    string status = 2;
}
```

### 3.2 与现有 AgentControlService 的关系

```protobuf
// 扩展现有 AgentControlService
service AgentControlService {
    // 现有接口
    rpc StartAgent(AgentRequest) returns (stream AgentState);
    rpc SubmitEvaluationResult(EvaluationResultRequest) returns (EvaluationResultResponse);
    rpc RequestShutdown(ShutdownRequest) returns (ShutdownResponse);
    rpc HealthCheck(HealthCheckRequest) returns (HealthCheckResponse);

    // 新增：获取评估器状态
    rpc GetEvaluatorStatus(EvaluatorStatusRequest) returns (EvaluatorStatusResponse);
}

message EvaluatorStatusRequest {
    string task_id = 1;
}

message EvaluatorStatusResponse {
    bool running = 1;
    int32 current_iteration = 2;
    int32 max_iterations = 3;
    string status = 4;
}
```

---

## 四、迭代控制流程

### 4.1 状态机定义

```
┌───────────────────────────────────────────────────────────────────────┐
│                    Agent 迭代状态机                                      │
│                    (迭代计数由 Evaluator 记录)                           │
│                                                                       │
│  ┌──────────┐                     ┌──────────┐                      │
│  │ RUNNING  │ ──执行完成─────────▶│EVAL_WAIT │                      │
│  └──────────┘                     └─────┬────┘                      │
│                                          │                             │
│                                          │ 评估                        │
│                                          ▼                             │
│         ┌─────────────────────────────────────────────────────────┐    │
│         │                    EVAL_WAIT                           │    │
│         │         (Evaluator 记录迭代次数，决定下一状态)            │    │
│         │                                                         │    │
│         │    ┌──────────────┐  ┌──────────────┐  ┌──────────┐  │    │
│         │    │  评估通过     │  │ 评估不通过    │  │ 达到最大  │  │    │
│         │    │  next_state  │  │ +有剩余迭代   │  │ 迭代次数  │  │    │
│         │    │   =DONE      │  │ =IMPROVING   │  │ =FAIL    │  │    │
│         │    └──────┬───────┘  └──────┬───────┘  └─────┬────┘  │    │
│         │           │                   │                │        │    │
│         └───────────┼───────────────────┼────────────────┼────────┘    │
│                     │                   │                │              │
│                     ▼                   ▼                ▼              │
│               ┌────────┐         ┌───────────┐     ┌──────────┐       │
│               │  DONE  │         │ IMPROVING │     │   FAIL  │       │
│               └────────┘         └───────────┘     └──────────┘       │
│               can_shutdown=true  should_continue=true  can_shutdown   │
└───────────────────────────────────────────────────────────────────────┘

状态说明：
- RUNNING: Agent 正在执行任务
- EVAL_WAIT: Agent 执行完成，Evaluator 评估中（记录迭代次数）
- IMPROVING: 评估不通过，Agent 根据反馈改进后重新执行
- DONE: 评估通过，任务完成
- FAIL: Evaluator 记录达到最大迭代次数，任务失败
```

### 4.2 简化的数据流（Python 只发不管）

```
Python 端                                    Rust 容器 (自主控制)
   │                                             │
   │ 1. StartAgent(task)                      │
   │    + eval_plan                            │
   │ ─────────────────────────────────────────▶│
   │                                             │
   │           === Rust 内部自主执行 ===        │
   │                                             │
   │  [IDLE] → [RUNNING] → [EVAL_WAIT]       │
   │       → [IMPROVING] → [EVAL_WAIT] ...   │
   │       → [DONE] / [FAIL]                 │
   │                                             │
   │           === 迭代完成 ===                │
   │                                             │
   │ 2. Evaluator 返回最终结果                 │
   │◀───────────────────────────────────────── │
   │    (包含最终评分、反馈、日志)              │
   │                                             │
   │ 3. Python 收集结果                        │
   │ 4. Python 主动关闭容器                    │
   │                                             │
   │
   └─ Python 在整个过程中不发送任何指令
      只通过日志监测执行进度
```

**关键变化**：
- Python 发送 `StartAgent` 后**不再发送任何指令**
- Rust 容器内部自主完成迭代控制
- Python 只在**最终结果返回**时接收数据

**关键流程说明：**

1. **EVAL_WAIT 触发执行结束**：Evaluator 在评估完成后，通过 `next_state` 字段明确告诉 Agent 接下来应该进入什么状态
2. **Evaluator 控制迭代**：不是 Agent 自己决定执行完成，而是 Evaluator 评估后决定：
   - `next_state = "DONE"` → 执行结束，可以关闭容器
   - `next_state = "IMPROVING"` → 需要继续改进，Agent 收到后重新执行
   - `next_state = "FAIL"` → 达到最大迭代，执行失败
3. **Python 根据 can_shutdown 决定是否关闭容器**：评估通过时 `can_shutdown=true`，Python 可以安全关闭容器

### 4.3 状态转换规则

```
┌─────────────────────────────────────────────────────────────────┐
│  状态转换矩阵                                                    │
├───────────────┬────────────────────────────────────────────────┤
│   当前状态    │                 下一状态                         │
│               ├─────────────┬──────────────┬───────────────┤
│               │ 评估通过    │ 评估不通过   │ 最大迭代      │
│               │             │ +有剩余      │ 超过          │
├───────────────┼─────────────┼──────────────┼───────────────┤
│  RUNNING      │  -         │  -           │  -            │
│  (执行中)     │             │              │               │
├───────────────┼─────────────┼──────────────┼───────────────┤
│  EVAL_WAIT    │   DONE     │  IMPROVING   │   FAIL        │
│  (评估中)     │ can_shutdown=true│should_continue=true│should_continue=false│
│               │             │              │               │
└───────────────┴─────────────┴──────────────┴───────────────┘
```

**Evaluator 评估逻辑伪代码：**

```rust
fn evaluate(&self, plan: &EvalPlanInfo, result: &ExecutionResult, iteration: i32) -> EvalResponse {
    // 1. 按维度评估
    let dimension_results = self.evaluate_dimensions(plan, result).await;

    // 2. 计算综合评分
    let overall_score = self.calculate_weighted_score(&dimension_results);

    // 3. 判断是否通过（所有维度通过）
    let passed = dimension_results.iter().all(|r| r.passed);

    // 4. 由 Evaluator 决定下一状态（基于迭代计数）
    let (next_state, can_shutdown) = if passed {
        ("DONE".to_string(), true)  // 评估通过
    } else if iteration >= plan.max_iterations {
        ("FAIL".to_string(), true)  // 达到最大迭代次数（Evaluator 记录）
    } else {
        ("IMPROVING".to_string(), false)  // 继续改进
    };

    EvalResponse {
        passed,
        overall_score,
        next_state,
        can_shutdown,
        should_continue: !passed && iteration < plan.max_iterations,
        remaining_iterations: plan.max_iterations - iteration,
        iteration,  // 当前迭代次数（由 Evaluator 返回）
        // ...
    }
}
```

**关键设计要点：**

- **迭代计数在 Evaluator**：每次评估后 `iteration` +1，由 Evaluator 跟踪
- **EVAL_WAIT 是决策中心**：所有状态转换都从 EVAL_WAIT 出发
- **明确的下一步信号**：`next_state` 字段告诉 Agent 应该进入什么状态
- **可关闭信号**：`can_shutdown=true` 时 Python 才能安全关闭容器

### 4.3 迭代控制逻辑

```rust
// evaluator.rs - 迭代控制器

impl EvaluatorService {
    async fn evaluate_stream(
        &self,
        mut events: Receiver<EvaluatorEvent>,
        response: Sender<EvalResponse>,
    ) {
        let mut iteration = 0;
        let mut current_plan: Option<EvalPlanInfo> = None;
        let mut latest_result: Option<ExecutionResult> = None;

        while let Some(event) = events.recv().await {
            match event.event_type {
                Some(EventType::Plan(plan)) => {
                    current_plan = Some(plan);
                    continue;
                }
                Some(EventType::Result(result)) => {
                    latest_result = Some(result);
                    iteration += 1;
                }
                None => continue,
            }

            // 执行评估
            let eval_response = self.evaluate(
                current_plan.as_ref().unwrap(),
                latest_result.as_ref().unwrap(),
                iteration,
            ).await;

            // 发送评估结果
            response.send(eval_response).await;

            // 检查是否继续
            if !eval_response.should_continue {
                break;
            }
        }
    }

    async fn evaluate(
        &self,
        plan: &EvalPlanInfo,
        result: &ExecutionResult,
        iteration: i32,
    ) -> EvalResponse {
        // 1. 按维度评估
        let mut dimension_results = Vec::new();
        for dim in &plan.dimensions {
            let dim_result = self.evaluate_dimension(dim, result).await;
            dimension_results.push(dim_result);
        }

        // 2. 计算综合评分
        let overall_score = self.calculate_weighted_score(
            &dimension_results,
            &plan.dimensions,
        );

        // 3. 判断是否通过
        let passed = dimension_results.iter().all(|r| r.passed);

        // 4. 生成反馈
        let feedback = self.generate_feedback(&dimension_results);

        // 5. 决定是否继续
        let should_continue = !passed && iteration < plan.max_iterations;

        EvalResponse {
            task_id: result.task_id.clone(),
            iteration,
            passed,
            overall_score,
            results: dimension_results,
            feedback,
            should_continue,
            remaining_iterations: plan.max_iterations - iteration,
            status: if passed { "success".to_string() } else { "improving".to_string() },
        }
    }
}
```

---

## 五、与现有系统集成

### 5.1 现有组件

| 组件 | 位置 | 状态 |
|------|------|------|
| AgentControlService | rust/ironclaw-sandbox/ | 已实现 |
| AgentServiceImpl | rust/ironclaw-sandbox/src/agent_service.rs | 已实现 |
| SecurityService | rust/ironclaw-sandbox/src/server.rs | 已实现 |
| EvalPlanner | src/evaluation/planner.py | 已实现 |
| EvaluationCoordinator | src/agents/evaluation_coordinator.py | 已实现 |

### 5.2 新增组件

| 组件 | 位置 | 描述 |
|------|------|------|
| EvaluatorService | rust/ironclaw-sandbox/src/evaluator.rs | 新增 |
| evaluator.proto | rust/ironclaw-sandbox/proto/ | 新增 |
| EvaluatorClient | src/runtime/evaluator_client.py | 新增 |

### 5.3 集成点

```python
# src/runtime/evaluator_client.py
class EvaluatorClient:
    """Rust 容器内评估器客户端"""

    def __init__(self, channel):
        self.stub = evaluator_pb2_grpc.EvaluatorServiceStub(channel)

    async def evaluate_stream(
        self,
        task_id: str,
        eval_plan: dict,
        execution_results: List[dict],
    ) -> AsyncIterator[EvalResponse]:
        """评估迭代流"""

        # 1. 发送评估计划
        yield evaluator_pb2.EvaluatorEvent(
            task_id=task_id,
            iteration=0,
            event_type=evaluator_pb2.EvaluatorEvent.Plan(
                plan=evaluator_pb2.EvalPlanInfo(
                    task_description=eval_plan["task_description"],
                    task_type=eval_plan["task_type"],
                    complexity=eval_plan["complexity"],
                    max_iterations=eval_plan["max_iterations"],
                    dimensions=[
                        evaluator_pb2.EvalDimensionInfo(
                            name=d["name"],
                            weight=d["weight"],
                            threshold=d["threshold"],
                            criteria=d["criteria"],
                            evaluation_method=d["evaluation_method"],
                        )
                        for d in eval_plan["dimensions"]
                    ],
                ),
            ),
        )

        # 2. 发送执行结果
        for i, result in enumerate(execution_results):
            yield evaluator_pb2.EvaluatorEvent(
                task_id=task_id,
                iteration=i + 1,
                event_type=evaluator_pb2.EvaluatorEvent.Result(
                    result=evaluator_pb2.ExecutionResult(
                        step=result.get("step", 0),
                        action=result.get("action", ""),
                        output=result.get("output", ""),
                    ),
                ),
            )
```

---

## 六、LLM 中间层设计 (Jeff Dean 原则) - Rust 容器内

### 6.1 LLM 中间层架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Rust 容器内 LLM 中间层                              │
│                    (统一管理 Target Agent 和 Evaluator 的 LLM 调用)    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    连接池管理器                                │   │
│  │   - 每个模型维护独立连接池                                   │   │
│  │   - 空闲连接复用                                            │   │
│  │   - 最大连接数限制                                          │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    熔断器 (Circuit Breaker)                  │   │
│  │   - 连续 N 次失败 → 熔断                                    │   │
│  │   - 熔断期间快速失败                                         │   │
│  │   - 定时探测恢复                                             │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌──────────────────────────────┐  ┌───────────────────────────┐  │
│  │       Target Agent            │  │       Evaluator           │  │
│  │       (LLM 调用者 #1)        │  │       (LLM 调用者 #2)     │  │
│  │  - 任务执行                   │  │  - 评估判断                │  │
│  │  - 工具调用                   │  │  - 结果分析                │  │
│  │  - 模型: 可配置               │  │  - 模型: 通常用更好模型    │  │
│  └──────────────────────────────┘  └───────────────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘

注: Default Agent 在 Python 端，不在 Rust 容器内
```

### 6.2 LLM 中间层接口

```rust
// llm_middleware.rs

/// LLM 中间层 trait
pub trait LLMGateway: Send + Sync {
    /// 发送聊天请求
    async fn chat(&self, request: ChatRequest) -> Result<ChatResponse, LLMError>;

    /// 获取连接池状态
    fn get_stats(&self) -> LLMStats;
}

/// 模型配置
pub struct ModelConfig {
    pub name: String,           // 模型名称
    pub endpoint: String,       // API 端点
    pub api_key: String,        // API 密钥
    pub max_connections: u32,   // 最大连接数
    pub timeout_secs: u64,       // 超时时间
}

/// 熔断器配置
pub struct CircuitBreakerConfig {
    pub failure_threshold: u32,  // 触发熔断的失败次数
    pub recovery_timeout: u64,  // 熔断恢复时间(秒)
    pub half_open_requests: u32, // 半开状态请求数
}
```

### 6.3 评估提示词 (复用 SWE-bench/AgentBench 最佳实践)

```python
# 复用 src/evaluation/prompts.py 中的完整模板

EVALUATION_PROMPT = """
# 角色
你是一个专业的 AI Agent 评估专家。你的任务是根据多个评估维度，对 Agent 的执行结果进行全面评估。

# 背景
OpenYoung 是一个 AI Agent 执行平台，会在 Rust 容器中运行目标 Agent，
并需要评估其执行质量。评估结果将用于判断 Agent 是否需要改进。

# 评估维度
{dimensions}

# 任务描述
{task_description}

# 执行结果
## Agent 输出
{agent_output}

## 执行轨迹
{trace}

# 评估标准
{criteria}

# 评估方法
{method}

# 输出格式
请输出以下 JSON 结构：

```json
{
  "dimension_results": [
    {
      "dimension": "correctness",
      "score": 0.85,
      "passed": true,
      "reasoning": "详细推理过程",
      "evidence": ["具体证据1", "具体证据2"]
    }
  ],
  "overall_score": 0.82,
  "passed": true,
  "feedback": "改进建议（如果未通过）",
  "confidence": 0.9
}
```

# 重要提醒
1. 每个维度都需要提供详细的 reasoning
2. score 必须是 0.0-1.0 之间的浮点数
3. 如果任何必需维度未通过，passed 应为 false
4. feedback 应具体、可操作
"""
```

---

## 七、结构化日志设计 (Cindy Sridharan 原则)

### 7.1 日志格式 (JSON 结构化)

```json
{
  "timestamp": "2026-03-10T18:30:00.000Z",
  "level": "INFO",
  "component": "target_agent",
  "event": "agent_started",
  "trace_id": "task-12345",
  "data": {
    "task_type": "coding",
    "model": "claude-sonnet-4-20250514"
  }
}
```

### 7.2 关键事件定义

| 事件 | 级别 | 说明 |
|------|------|------|
| `agent_started` | INFO | Target Agent 启动 |
| `agent_thinking` | DEBUG | Agent 思考中 |
| `agent_action` | INFO | Agent 执行动作 |
| `agent_observation` | INFO | Agent 收到观察 |
| `agent_completed` | INFO | Agent 执行完成 |
| `evaluator_started` | INFO | Evaluator 开始评估 |
| `evaluator_dimension` | DEBUG | 评估单个维度 |
| `evaluator_iteration` | INFO | 评估迭代 |
| `evaluator_completed` | INFO | 评估完成 |
| `iteration_passed` | INFO | 迭代通过 |
| `iteration_failed` | WARN | 迭代未通过 |
| `max_iterations_reached` | WARN | 达到最大迭代 |
| `task_success` | INFO | 任务成功 |
| `task_failed` | ERROR | 任务失败 |

### 7.3 Python 日志消费者

```python
# src/runtime/log_consumer.py
import json
import asyncio
from typing import AsyncIterator

class LogConsumer:
    """消费 Rust 容器日志，实现可视化监测"""

    def __init__(self, log_stream: AsyncIterator[bytes]):
        self.stream = log_stream

    async def events(self) -> AsyncIterator[dict]:
        """解析日志事件流"""
        async for raw in self.stream:
            if not raw:
                continue
            try:
                yield json.loads(raw)
            except json.JSONDecodeError:
                continue

    async def monitor_agent_progress(self, task_id: str) -> dict:
        """监测 Agent 进度"""
        events = []
        async for event in self.events():
            if event.get("trace_id") == task_id:
                events.append(event)
                # 检查是否完成
                if event["event"] in ["task_success", "task_failed"]:
                    break
        return self.summarize(events)
```

---

## 八、实施计划

### 6.1 评估器 LLM 调用

```rust
// llm_client.rs
pub struct LLMClient {
    api_key: String,
    endpoint: String,
    client: reqwest::Client,
}

impl LLMClient {
    pub async fn chat(&self, prompt: String) -> Result<String, LLMError> {
        let response = self.client
            .post(&self.endpoint)
            .header("Authorization", format!("Bearer {}", self.api_key))
            .json(&json!({
                "model": "claude-sonnet-4-20250514",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 4096,
            }))
            .send()
            .await?;

        let result: serde_json::Value = response.json().await?;
        Ok(result["choices"][0]["message"]["content"].as_str().unwrap())
    }
}
```

### 6.2 评估提示词 (复用现有)

```python
# 复用 src/evaluation/prompts.py 中的提示词
EVALUATION_PROMMPT = """
# 角色
你是一个专业的 AI Agent 评估专家。

# 评估维度
{dimensions}

# 执行结果
{output}

# 评估标准
{criteria}

# 输出格式
请输出 JSON：
{{
    "score": 0.0-1.0,
    "passed": true/false,
    "feedback": "评估反馈"
}}
"""
```

---

## 九、实施计划

### 9.1 阶段一：Proto 定义和基础服务

| 任务 | 文件 | 描述 |
|------|------|------|
| 1.1 | proto/evaluator.proto | 定义 EvaluatorService 接口 |
| 1.2 | src/evaluator.rs | 实现 EvaluatorService |
| 1.3 | build.rs | 编译新 proto |
| 1.4 | server.rs | 注册 EvaluatorService |

### 9.2 阶段二：LLM 中间层

| 任务 | 文件 | 描述 |
|------|------|------|
| 2.1 | src/llm_middleware.rs | LLM 中间层 |
| 2.2 | src/llm_client.rs | LLM 调用客户端 |
| 2.3 | src/circuit_breaker.rs | 熔断器 |

### 9.3 阶段三：评估逻辑

| 任务 | 文件 | 描述 |
|------|------|------|
| 3.1 | src/evaluator/dimension.rs | 维度评估逻辑 |
| 3.2 | src/evaluator/iterations.rs | 迭代控制器 |

### 9.4 阶段四：日志和 Python 集成

| 任务 | 文件 | 描述 |
|------|------|------|
| 4.1 | src/logging.rs | 结构化日志 |
| 4.2 | src/runtime/evaluator_client.py | Python 客户端 |
| 4.3 | src/runtime/log_consumer.py | 日志消费者 |
| 4.4 | integration test | 集成测试 |

---

## 十、测试设计

### 8.1 单元测试

```python
def test_evaluator_accepts_plan():
    """评估计划正确传递给评估器"""

def test_evaluator_passes_good_code():
    """正确代码通过评估"""

def test_evaluator_fails_bad_code():
    """错误代码返回改进建议"""

def test_evaluator_max_iterations():
    """超过最大迭代次数停止"""

def test_evaluator_llm_failure():
    """LLM 调用失败处理"""

def test_evaluator_timeout():
    """评估超时处理"""
```

---

## 九、风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| LLM API 延迟高 | 评估时间长 | 添加超时和重试 |
| 评估结果不稳定 | 同一代码不同分数 | 多次评估取平均 |
| 迭代无限循环 | 容器资源耗尽 | 强制最大迭代次数 |

---

## 十、总结

本设计基于以下顶级专家方法论：

1. **Leslie Lamport 状态机**：迭代控制在 Evaluator 内部闭环
2. **Jeff Dean 横向扩展**：Evaluator 无状态设计
3. **Rob Pike 简洁接口**：gRPC 双向流统一通信
4. **John Ousterhout 增量交付**：分阶段实施

---

*文档版本: 1.0*
*设计基于: 2026-03-10 讨论*

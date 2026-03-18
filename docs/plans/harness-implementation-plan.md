# AI Software Factory — Harness 实施方案

## 背景

基于行业最佳实践（Anthropic、LangChain、OpenAI Codex），Harness 不是 Pipeline 的一个 Stage，而是**贯穿全局的基础设施层**。本计划将现有分散的评估组件整合升级为完整的 Evaluation Harness。

## 现状盘点

| 模块 | 职责 | 可复用度 | 缺口 |
|------|------|----------|------|
| `datacenter/quality.py` (435行) | 6维度静态评估 | ★★★★ | 无任务执行、无pass@k |
| `datacenter/tracing.py` (310行) | OTEL/LangSmith追踪 | ★★★★★ | 未与评估集成 |
| `datacenter/store.py` | 数据存储 | ★★★ | 需扩展为评估存储 |
| `hub/evaluate/evaluator.py` (191行) | Badge系统 | ★★★ | 展示层、需统一 |
| `core/agent_checkpoint.py` (315行) | PostgreSQL检查点 | ★★★ | 硬依赖PG、无轻量方案 |
| `core/langgraph_state.py` (139行) | Agent状态 | ★★★★ | 已有evaluation_score字段 |

## 目标架构

```
src/hub/evaluate/
├── benchmark.py         # [NEW] 基准测试定义 (Task, TaskSuite, GraderType)
├── runner.py           # [NEW] 评估执行引擎
├── harness.py          # [NEW] Evaluation Harness (核心编排器)
├── graders/
│   ├── __init__.py
│   ├── code.py        # [NEW] Code-Based Grader (lint/测试/状态检查)
│   ├── model.py        # [NEW] Model-Based Grader (LLM-as-Judge)
│   └── human.py        # [NEW] Human Grader (人工判定)
├── metrics.py          # [NEW] pass@k / latency / cost 指标
├── middleware.py       # [NEW] Harness Middleware (ContextEngineering, LoopDetection, PreCompletionCheck)
└── entropy.py         # [NEW] Entropy Management (熵管理)

src/core/
├── langgraph_state.py # [UPGRADE] 添加 benchmark_id / ground_truth / expected_output
└── agent_checkpoint.py # [UPGRADE] 添加 score / benchmark_id 字段，轻量存储

src/datacenter/
├── tracing.py          # [UPGRADE] 添加 eval-specific span 类型
└── store.py           # [UPGRADE] 评估结果持久化
```

## Phase 1: 核心基础设施 (P0)

### 1.1 定义评估核心数据结构 (`src/hub/evaluate/benchmark.py`)

```python
# Grader类型枚举
class GraderType(Enum):
    CODE_BASED = "code"      # 确定性检查
    MODEL_BASED = "model"    # LLM评判
    HUMAN = "human"          # 人工判定

# 单个任务
@dataclass
class BenchmarkTask:
    id: str
    desc: str
    prompt: str
    graders: list[dict]      # grader配置
    expected_output: Optional[str]
    timeout_sec: int = 300
    tags: list[str] = field(default_factory=list)

# 任务套件
@dataclass
class TaskSuite:
    id: str
    name: str
    tasks: list[BenchmarkTask]
    metadata: dict

# Eval类型
class EvalType(Enum):
    CAPABILITY = "capability"    # 探索能力边界
    REGRESSION = "regression"    # 保护已有功能
```

### 1.2 实现 Grader 体系 (`src/hub/evaluate/graders/`)

**Code-Based Grader:**
- 单元测试运行 + pass/fail
- Lint (ruff/mypy/bandit)
- 工具调用验证
- 状态检查 (环境最终状态)
- 阈值: pass^3 = 100% (regression), pass@3 >= 90% (capability)

**Model-Based Grader:**
- Rubric打分 (结构化评分标准)
- 成对比较
- 自然语言断言

**Human Grader:**
- 人工判定接口
- 交叉校准

### 1.3 实现评估执行引擎 (`src/hub/evaluate/runner.py`)

```python
class EvalRunner:
    async def run_task(task: BenchmarkTask, agent, n_trials: int = 3)
        → list[EvalTrial]

    async def run_suite(suite: TaskSuite, agent, n_trials: int = 3)
        → EvalReport

class EvalTrial:
    task_id: str
    transcript: list[dict]      # 完整执行轨迹
    outcome: dict                # 最终环境状态
    grader_results: list[dict]  # 各grader结果
    metrics: TrialMetrics       # latency, tokens, cost
    passed: bool
```

### 1.4 实现 pass@k 指标 (`src/hub/evaluate/metrics.py`)

```python
@dataclass
class EvalMetrics:
    pass_at_1: float
    pass_at_3: float
    pass_at_k: float
    pass_rate: float           # pass^k (全部成功)
    avg_latency_ms: float
    avg_cost_usd: float
    total_trials: int

def compute_pass_at_k(results: list[bool], k: int) → float:
    """计算 pass@k = 1 - C(n-k, k) / C(n, k)"""

def compute_pass_rate(results: list[bool]) → float:
    """计算 pass^all = 全部成功才通过"""
```

## Phase 2: Harness 编排层 (P1)

### 2.1 Evaluation Harness 核心 (`src/hub/evaluate/harness.py`)

```python
class EvaluationHarness:
    """评估基础设施 - 贯穿 Plan/Code/Test 各Stage"""

    def __init__(self, graders: list[Grader], middleware: list[HarnessMiddleware]):
        self.graders = graders
        self.middleware = middleware
        self.tracer = get_tracing_manager()
        self.checkpoint_mgr = get_checkpoint_manager()

    async def evaluate(self, task: BenchmarkTask, agent) → EvalTrial:
        # Middleware前置处理
        for mw in self.middleware:
            await mw.before_task(task, agent)

        # 执行任务
        trial = await self.runner.run_task(task, agent, n_trials=3)

        # Middleware后置处理
        for mw in reversed(self.middleware):
            await mw.after_task(trial)

        # 持久化
        await self.checkpoint_mgr.save_eval_result(trial)
        await self.tracer.export_eval_span(trial)

        return trial
```

### 2.2 Middleware 链

| Middleware | 职责 | 对应行业实践 |
|-----------|------|-------------|
| `ContextEngineeringMiddleware` | 注入代码库映射 / AGENTS.md | OpenAI/LangChain |
| `LoopDetectionMiddleware` | 检测重复编辑、doom loops | LangChain |
| `PreCompletionCheckMiddleware` | 提交前自验证清单 | LangChain |
| `ArchitecturalConstraintMiddleware` | 架构约束强制 | OpenAI |
| `ReasoningSandwichMiddleware` | 计划用高推理，落地用低推理 | OpenAI |

## Phase 3: Capability / Regression 双轨 (P1)

### 3.1 Capability Eval Suite

针对 AI Software Factory 核心能力：
- **Plan**: 需求完整性、可验证性
- **Code**: 代码正确性、架构合规
- **Test**: 测试覆盖率、行为正确性
- **Feedback**: 改进触发正确性

### 3.2 Regression Eval Suite

保护已有功能：
- CLI 命令执行
- WebUI 页面渲染
- API 响应正确性

## Phase 4: Entropy Management (P2)

- 文档一致性检查
- 约束违规扫描
- 死代码清理
- 依赖审计

## 实施顺序

```
Week 1: Phase 1 (核心数据结构 + Graders + Runner)
  → src/hub/evaluate/benchmark.py
  → src/hub/evaluate/graders/code.py
  → src/hub/evaluate/graders/model.py
  → src/hub/evaluate/graders/human.py
  → src/hub/evaluate/runner.py
  → src/hub/evaluate/metrics.py

Week 2: Phase 2 (Harness + Middleware)
  → src/hub/evaluate/harness.py
  → src/hub/evaluate/middleware.py

Week 3: Phase 3 (Capability/Regression Suite)
  → 定义并实现评估套件
  → 集成到 CI

Week 4: Phase 4 (Entropy Management)
  → src/hub/evaluate/entropy.py
```

## 关键技术决策

1. **PostgreSQL 硬依赖 → 轻量方案**: `AgentCheckpoint` 增加 SQLite fallback 用于本地评估
2. **无任务执行 → Sandbox 执行**: 利用现有 sandbox 机制执行 BenchmarkTask
3. **分散评估 → 统一 Harness**: 将 `datacenter/quality.py` 重构为 Harness 的一个 Grader
4. **无 pass@k → 指标追踪**: 新建 metrics.py，持续记录 pass@k 趋势

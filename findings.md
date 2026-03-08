# Findings

---

## 2026-03-07: 项目深度分析

### 架构分析

#### 1. YoungAgent 职责过于臃肿
- **问题**: 单文件 1442 行，远超 500 行限制
- **影响**: 难以测试、维护、扩展
- **建议**: 拆分为 TaskExecutor, PermissionEvaluator, ToolDispatcher, EvaluationCoordinator

#### 2. EvaluationHub 设计定位模糊
- **设计文档**: 纯包仓库，不执行评估
- **实际代码**: 包含评估执行逻辑
- **建议**: 落实设计或更新文档

#### 3. package_manager 模块膨胀
- **问题**: 24 个文件，涵盖导入、评估、分析
- **影响**: 违反 DDD 原则，职责混乱
- **建议**: 按领域划分为 importers/, evaluators/, analyzers/

#### 4. LLM 客户端重复
- **client_adapter.py**: LLMClient
- **unified_client.py**: UnifiedLLMClient
- **建议**: 选择一个作为主客户端

#### 5. 数据类型不统一
- **core/types.py**: Agent, Task, Message
- **datacenter/**: TraceRecord, MemoryItem, Tenant
- **evaluation/**: EvaluationDimension, EvalLevel
- **建议**: 建立统一模型层

#### 6. DataCenter 数据模型重复
- TraceRecord (datacenter.py) vs RunRecord (run_tracker.py)
- 存储方案不统一 (SQLite + JSON + SQLAlchemy)

### 模块配合问题

| 模块 | 问题 |
|------|------|
| YoungAgent → LLM | 两个客户端混用 |
| YoungAgent → EvaluationHub | 评估逻辑嵌入业务流程 |
| YoungAgent → DataCenter | 多处独立存储 |
| package_manager → others | 功能未被充分使用 |

---

## Research

### Always Skills 机制
- Always Skills 在 Agent 启动时自动加载，无需用户触发
- 从 `src/skills/` 目录加载
- 技能通过 `skill.yaml` 定义元数据

### 技能加载架构
- **Always Skills**: 从 `src/skills/{skill_name}/` 加载
- **Regular Skills**: 从 `packages/skill-{name}/` 加载
- 加载流程: `_load_skills()` → `_build_skill_prompt()`

### Skill YAML 格式
```yaml
name: "skill-name"
description: "技能描述"
entry: "SKILL.md"
version: "1.0.0"
tags:
  - utility
always: false  # 是否作为 always_skills
```

## Technical Decisions

### 核心文件修改
1. `src/core/types.py` - 添加 `always_skills` 字段
2. `src/cli/main.py` - 添加配置解析
3. `src/agents/young_agent.py` - 实现加载逻辑
4. `src/agents/default.yaml` - 配置 always_skills

### 技能来源
- 内置: self-improvement, find-skills, summarize
- 包: github-import, coding-standards, eval-planner

## Notes
- 测试结果显示 find-skills 和 summarize 都能正常工作
- 文档已更新到 v1.1.0
- 智能路由已实现并测试通过

### 智能路由实现
- URL 检测 → summarize 技能
- "如何" / "how to" → find-skills 技能
- 技能请求检测 → 对应技能
- **导入意图排除**: 当用户说"导入"、"克隆"时，URL 不会路由到 summarize，让 github-import 处理

---

## 2026-03-07: 执行 R1-1 拆分 YoungAgent

### 已完成

1. **创建 EvaluationCoordinator** (`src/agents/evaluation_coordinator.py`)
   - 提取评估逻辑（264行）
   - 包含：LLMJudge调用、completion_rate计算、阈值检查、动态权重

2. **修改 young_agent.py**
   - 从1442行减少到1294行（-148行）
   - 使用EvaluationCoordinator进行评估

### 测试结果

```
python3 -m src.cli.main run default "你好"
Score: 0.94
Evaluator: task_completion
task_type: general
```

### 后续任务

- 继续拆分为 TaskExecutor（任务执行逻辑）
- 统一 LLM 客户端（R1-2）
- 更新设计文档说明当前架构（R1-3）

### 2026-03-07: R1-2 & R1-3 分析

#### R1-2: LLM 客户端分析

**发现**:
- `client.py` (LLMClient): 完整实现，支持 5 个 provider (deepseek, openai, moonshot, qwen, glm)，支持 tool calling，但**未被使用**
- `client_adapter.py` (LLMClient): 被广泛使用（agents, evaluation），内部使用 unified_client.py
- `unified_client.py` (UnifiedLLMClient): 被 client_adapter.py 依赖

**问题**: 死代码存在

**决策**: 暂不处理（风险高）

#### R1-3: EvaluationHub 分析 ✅ 已完成

**发现**:
- 设计文档：EvaluationHub 应为纯包仓库
- 实际：包含 evaluate(), evaluate_full() 等执行逻辑

**决策**:
- 评估执行逻辑已提取到 EvaluationCoordinator
- 更新设计文档 (evaluation-hub-design.md) 到 v3.2

**更新内容**:
- 添加架构变更说明 (0. 架构变更说明)
- 更新协作者说明
- 明确 EvaluationCoordinator 负责执行，EvaluationHub 负责存储

### 2026-03-07: R2-2 数据类型统一

**发现**:
- MessageRole 在两个地方定义: core/types.py, channels/base.py
- 已添加类型别名解决重复问题

**执行**:
- 修改 channels/base.py 使用 core/types.MessageRole
- 保持向后兼容

### 2026-03-07: 2026 AI Agent 最佳实践实施

#### P0-1: Tool Contract 验证层 ✅

**实现**:
- 新建 `src/tools/contract.py` (207行)
- 定义 `ToolContract`, `FieldSchema`, `ToolContractRegistry`
- 支持类型验证、正则验证、枚举验证、范围验证
- 集成到 `ToolExecutor.execute()`

**效果**:
- 工具输入类型验证 (string/integer/boolean/array)
- 必填字段检查
- 正则模式匹配
- 枚举值验证
- 范围检查

#### P0-2: LLM 客户端分析 ✅

**发现**:
- `client.py`: 完整实现，支持 5 个 provider，未被使用 (死代码)
- `client_adapter.py`: 当前使用，包装 `unified_client.py`

**决策**: 保持现状，风险太高，文档记录

#### P1-2: Tracing 基础设施 ✅

**实现**:
- 新建 `src/tools/tracing.py` (217行)
- 定义 `Tracer`, `Span`, `SpanKind`, `SpanStatus`
- 支持步骤级 spans
- 上下文管理器支持
- 导出到 JSON

**集成**: 已集成到 `ToolExecutor.execute()`

#### P1-3: 评估数据集扩充 ✅

**实现**:
- 新建 `src/evaluation/dataset.py` (21个测试用例)
- 覆盖 6 种任务类型
- 覆盖 3 种难度
- 覆盖 3 个领域

#### 2026 最佳实践对照

| 实践 | 状态 |
|------|------|
| Tool Contracts | ✅ 已实现 |
| State Reducer | ⚠️ 部分 |
| Tracing | ✅ 已实现 |
| Policy Gating | ✅ 已实现 |
| Memory Layers | ⚠️ 基础 |
| Eval Dataset (20+) | ✅ 已实现 (21用例) |
| Tracing | ✅ 已实现 (基础) |
| Policy Gating | ✅ 已实现 |
| Memory Layers | ⚠️ 基础 |
| EvalPlanner | ✅ 已实现 |

### 2026-03-07: 设计文档更新

**更新内容**:
- `docs/design/young-agent-core.md` → v1.1.0，添加 2026 最佳实践章节
- `docs/design/evaluation-hub-design.md` → v3.3，添加 EvalPlanner 说明

**新增组件文档**:
- EvalPlanner: 任务执行前自动生成评估计划
- EvaluationDataset: 21 个测试用例覆盖 6 种任务类型

### 2026-03-07: TaskExecutor 拆分

**实现**:
- 新建 `src/agents/task_executor.py` (143 行)
- 提取 YoungAgent 中的任务执行逻辑：
  - LLM 调用循环
  - 工具执行循环
  - FlowSkill 智能路由
  - SubAgent 委托
- 修改 `young_agent.py` 使用 TaskExecutor

**结果**:
- young_agent.py: 1311 → 1333 行 (+22 行初始化代码)
- 新增 task_executor.py: 143 行
- 任务执行逻辑已分离

### 2026-03-07: 数据类型分析

**发现**:
- MessageRole: 已统一 (channels/base.py → core/types)
- Message 类: 分析完成 - core/types 和 llm/types 用途不同
  - core/types.Message: 内部 agent 消息处理，使用 MessageRole enum
  - llm/types.Message: LLM API 通信，使用 str role

**决策**: 保持分离设计，用途不同

### 2026-03-07: R1-2 LLM 客户端统一

**实现**:
- 修改 `client.py` 为适配器，导入自 `client_adapter.py`
- 修改 `client_adapter.py` 支持新旧两种接口:
  - 新接口: `chat(messages, model=model)`
  - 旧接口: `chat(model, messages)`

**结果**:
- 所有测试通过 (5/5)
- 统一 LLM 客户端接口

### 2026-03-07: LLM Client 关键字参数修复

**问题**:
- 调用 `client.chat(model=..., messages=...)` 时报错
- 错误: `LLMClient._chat_impl() got multiple values for argument 'messages'`

**修复**:
- 在 `client_adapter.py` 的 `chat()` 方法中添加 `messages` 作为显式 keyword argument
- 优先检查 keyword argument，再检查 positional argument

**结果**:
- 所有测试通过 (5/5)

### 2026-03-07: R2-3 DataCenter 存储统一 - Phase 1

**实现**:
- 新建 `src/datacenter/execution_record.py` (195行)
- 定义 `ExecutionRecord` 统一数据模型
- 支持层级字段: execution_id, run_id, step_id
- 支持状态管理: mark_running(), mark_success(), mark_failed()
- 实现 `RecordAdapter` 适配器 (兼容现有 TraceRecord, RunRecord, StepRecord)

**模型设计**:
```python
@dataclass
class ExecutionRecord:
    execution_id: str
    run_id: Optional[str] = None
    step_id: Optional[str] = None
    agent_name: str = ""
    task_description: str = ""
    session_id: str = ""
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_ms: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float = 0.0
    status: str = "pending"
    error: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    steps: List[Dict[str, Any]] = field(default_factory=list)
```

**结果**:
- 模块导入测试通过
- 全流程测试通过 (5/5)

### 2026-03-07: R2-3 DataCenter 存储统一 - Phase 2

**实现**:
- 新建 `src/datacenter/unified_store.py` (180行)
- 实现 UnifiedStore 类，基于 BaseStorage
- 支持 CRUD: save, get, list_recent, list_by_status, update_status, delete
- 支持统计: get_stats()
- 支持索引: execution_id, run_id, session_id, status, start_time

**测试结果**:
- ✅ UnifiedStore 初始化成功
- ✅ 保存/查询记录正常
- ✅ 状态更新正常
- ✅ 统计功能正常
- ✅ 全流程测试通过 (5/5)

### 2026-03-07: R2-3 DataCenter 存储统一 - 完成

**Phase 3: 集成**:
- 更新 `src/datacenter/__init__.py` 导出新模块
- 添加 ExecutionRecord, ExecutionStatus, RecordAdapter, UnifiedStore, get_unified_store

**Phase 4: 验证**:
- ✅ 所有模块导入成功
- ✅ 全流程测试通过 (5/5)

**最终结果**:
- R2-3 任务完成
- 新增文件: execution_record.py, unified_store.py
- 向后兼容: 现有模块无需修改

### 2026-03-07: R2-2-3 mypy 配置

**实现**:
- 添加 `[tool.mypy]` 配置到 `pyproject.toml`
- 配置检查选项: warn_return_any, check_untyped_defs 等
- 排除测试和文档目录

**注意**: 需要安装 mypy 才能运行类型检查

#XH|# Mightyoung 集成设计
#KM|
#BK|> 版本: 1.0.0
#BX|> 更新日期: 2026-03-01
#BT|

## 1. 项目重新定位

### 1.1 从"投标平台"到"Agent 库"

| 维度 | 当前 (投标平台) | 目标 (Agent 库) |
|------|---------------|----------------|
| **核心价值** | 多 Agent 协作生成投标文书 | 提供 Agent 范式模版 + 自进化能力 + 生态变现 |
| **用户** | 投标团队 | 开发者 / AI 工程师 / 行业用户 |
| **编排方式** | LangGraph 固定管线 + 状态机 | Flow Skill (基于状态激活) |
| **扩展方式** | 12 个硬编码 Agent | Agent 定义 + Skill 组合 + Package 生态 |
| **评估** | 投标质量评分 | 通用评估框架 + 业务规则模版 |
| **数据** | 投标文档处理 | 通用 DataSet 抽象 |
| **变现模式** | 无 | 价值提升层 Package 交易 |

### 1.2 核心设计原则

1. **Core = 零外部运行时依赖** — SQLite + 内存降级，开箱即用
2. **自进化在核心内** — growth/ 模块始终包含在 core 中
3. **Skill 替代 Workflow** — 工作流编排逻辑由 Flow Skill 实现
4. **前端仅展示** — 所有配置通过 `mightyoung.yaml` + `.env` 文件完成
5. **插件可卸载** — 安全、部署、通道等均为可选插件
6. **价值提升层高度解耦** — Package 与核心零耦合，傻瓜式嵌入

### 1.3 配置 Schema 定义

项目配置集中在 `mightyoung.yaml` 和 `.env` 两个文件，实现**零代码配置化**。

#### 1.3.1 配置文件分工

| 文件 | 职责 | 示例 |
|------|------|------|
| `.env` | 敏感信息 | API Keys, 数据库密码, Token |
| `mightyoung.yaml` | 业务配置 | Agent定义, Skill, DataSet, 评估规则 |

#### 1.3.2 配置加载优先级

| 优先级 | 来源 | 说明 |
|--------|------|------|
| 1 (最高) | 命令行参数 | `--config` 指定 |
| 2 | 环境变量 | `MIGHTYOUNG_CONFIG_PATH` |
| 3 | 当前目录 | `./mightyoung.yaml` (默认) |
| 4 | 用户目录 | `~/.mightyoung/config.yaml` |
| 5 (最低) | 系统目录 | `/etc/mightyoung/config.yaml` |

---

## 2. 三层设计哲学

每个支柱 (Agent / DataCenter / EvaluationCenter) 都遵循相同的三层结构：

```
┌────────────────────────────────────────────────────────────────────┐
│  价值提升层 (Value Enhancement)                                     │
│  定位: 行业/个人在项目壮大过程中持续积累价值                          │
│  演进: 开源社区 + 行业专家 贡献领域经验                              │
│  变现: 通过出售 Package 实现经验、数据与知识的获利                   │
│  要求: 与通用层【高度解耦 + 高度适配】                            │
│        快速、傻瓜式、无缝嵌入                                      │
│                                                                    │
│  Agent: 行业 Skill + Evolver 包 + 高质量Flow Skill                │
│  DataCenter: 行业数据集 / 专业数据库                               │
│  EvaluationCenter: 特定业务评估规则                                 │
└────────────────────────────────────────────────────────────────────┘
                           ▲ 高度适配
                           │ 零耦合
┌────────────────────────────────────────────────────────────────────┐
│  通用层 (General)                                                  │
│  定位: 提供基础模版和通用能力                                       │
│  演进: 核心团队维护 + 社区持续增强                                  │
│  开放: 开源，接受社区 PR                                            │
│                                                                    │
│  Agent: Agent 范式(继承体系) + MCP + Skills + Evolver(RL)         │
│  DataCenter: DataCenter Skill (通用调用逻辑)                       │
│  EvaluationCenter: 评估规则模版                                      │
└────────────────────────────────────────────────────────────────────┘
                           ▲ 标准接口
                           │ 社区协作
┌────────────────────────────────────────────────────────────────────┐
│  合作层 (Collaboration)                                            │
│  定位: 需要开源社区和互联网持续完善的部分                            │
│  演进: 社区驱动，集体智慧                                         │
│  开放: 完全开源，鼓励贡献                                          │
│                                                                    │
│  Agent: 通用 Skill 库 + 通用 MCP Server 库                         │
│  DataCenter: 数据集标准规范                                        │
│  EvaluationCenter: 权威行业级评估规则                               │
└────────────────────────────────────────────────────────────────────┘
```

### 层间关系核心约束

| 约束 | 说明 |
|------|------|
| **价值提升层 → 通用层**: 单向依赖 | 价值提升层 Package 依赖通用层接口，反之绝不 |
| **高度解耦**: Package 不修改核心代码 | 通过注册机制嵌入，不 import 核心内部实现 |
| **高度适配**: Package 遵循标准接口 | 核心暴露稳定的 Protocol/ABC，Package 实现它们 |
| **傻瓜式嵌入**: 一行代码加载 | `mightyoung install <package>` 或 `packages:` 配置项 |
| **零侵入卸载**: 一行代码移除 | `mightyoung uninstall <package>`，核心功能不受影响 |

---

## 3. 三大核心系统架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Mightyoung Agent Library                            │
│                                                                             │
│  ┌──────────────────────┐ ┌────────────────────┐ ┌──────────────────────┐ │
│  │    Agent 支柱         │ │  DataCenter 支柱   │ │  EvaluationCenter 支柱  │ │
│  │                      │ │                    │ │                      │ │
│  │ ┌──────────────────┐ │ │ ┌────────────────┐ │ │ ┌──────────────────┐ │ │
│  │ │ 💰 价值提升       │ │ │ │ 💰 价值提升     │ │ │ │ 💰 价值提升       │ │ │
│  │ │ · 行业 Skill      │ │ │ │ · 行业数据集   │ │ │ │ · 业务评估规则   │ │ │
│  │ │ · Evolver 包      │ │ │ │ · 专业数据库   │ │ │ │                  │ │ │
│  │ │ · Flow Skill      │ │ │ │                │ │ │ │                  │ │ │
│  │ │  (Package 发布)    │ │ │  (Package 发布) │ │ │  (Package 发布)   │ │ │
│  │ └──────────────────┘ │ │ └────────────────┘ │ │ └──────────────────┘ │ │
│  │                      │ │                    │ │                      │ │
│  │ ┌──────────────────┐ │ │ ┌────────────────┐ │ │ ┌──────────────────┐ │ │
│  │ │ 🔧 通用           │ │ │ │ 🔧 通用         │ │ │ │ 🔧 通用           │ │ │
│  │ │ · Agent 范式      │ │ │ · DataCenter API│ │ │ · BaseMetric     │ │ │
│  │ │ · MCP + Skills   │ │ │ · Provider      │ │ │ · 注册机制        │ │ │
│  │ │ · Evolver(RL)    │ │ │ · Loader        │ │ │ · LLM-as-Judge   │ │ │
│  │ └──────────────────┘ │ │ └────────────────┘ │ │ └──────────────────┘ │ │
│  │                      │ │                    │ │                      │ │
│  │ ┌──────────────────┐ │ │ ┌────────────────┐ │ │ ┌──────────────────┐ │ │
│  │ │ 🤝 合作           │ │ │ │ 🤝 合作         │ │ │ │ 🤝 合作           │ │ │
│  │ │ · 通用 Skill 库   │ │ │ · 标准规范      │ │ │ · 行业标准        │ │ │
│  │ │ · 通用 MCP        │ │ │ · 公开数据集   │ │ │ · 权威 Rubric    │ │ │
│  │ └──────────────────┘ │ │ └────────────────┘ │ │ └──────────────────┘ │ │
│  └──────────────────────┘ └────────────────────┘ └──────────────────────┘ │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                    Package 系统 (价值交付 + 生态变现)                   │ │
│  │  install / link / market / publish                                     │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────┐   │
│  │                         核心引擎 (Core)                             │   │
│  │     Agent + Skill + Trace + Budget + Pattern + Quality + Hooks      │   │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │   │
│  │  │  DataCenter 系统 (数据存储 + Harness)                           │  │   │
│  │  │  - Harness (数据获取方式: TraceLog, Metrics, FailurePattern)  │  │   │
│  │  │  - Memory (Episodic/Semantic/Working)                         │  │   │
│  │  │  - Checkpoints (状态恢复)                                     │  │   │
│  │  └─────────────────────────────────────────────────────────────────┘  │   │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │   │
│  │  │  Evolver 系统 (自进化)                                          │  │   │
│  │  │  - 六阶段循环 (Trace→Evaluate→Distill→Compile→Verify→Apply)  │  │   │
│  │  │  - 三级Capsule结构 (GENE.yaml / CAPSULE.md / META/)           │  │   │
│  │  │  - 知识蒸馏 (语义/情景/程序记忆)                                │  │   │
│  │  └─────────────────────────────────────────────────────────────────┘  │   │
│  └───────────────────────────────────────────────────────────────────┘
└─────────────────────────────────────────────────────────────────────────────┘
```

### 三大系统共享机制

KS|| 机制 | Agent | DataCenter | EvaluationCenter | Package |
|------|-------|-------------|----------------|---------|
| **三层映射** | 行业Skill/通用Skill/标准 | 行业DataSet/通用API/标准 | 行业规则/通用模版/标准 | - |
| **扩展方式** | Package (Skill/Evolver) | Package (Dataset) | Package (Evaluation) | - |
| **核心抽象** | BaseAgent | BaseDataCenter | BaseMetric | - |
| **配置** | skills: | datacenter: | evaluation: | packages: |
```

### 四大系统共享机制

| 机制 | Agent | DataSet | Evaluation | Package |
|------|-------|---------|------------|---------|
| **三层映射** | 行业Skill/通用Skill/标准 | 行业DataSet/通用API/标准 | 行业规则/通用模版/标准 | - |
| **扩展方式** | Package (Skill/Evolver) | Package (Dataset) | Package (Evaluation) | - |
| **核心抽象** | BaseAgent | BaseDataSet | BaseMetric | - |
| **配置** | skills: | datasets: | evaluation: | packages: |

---

## 4. Harness 系统设计 (上下文压缩)

### 4.1 锚定迭代摘要 (Anchored Iterative Summarization)

#### 4.1.1 核心概念

当前Harness的`_generate_history_summary`仅做简单截断（每条消息100字符），无法满足：
- 语义压缩（减少token）
- 结构化（可检索）
- 经验提取（供Evolver使用）

采用**锚定迭代摘要**策略（基于OpenCode模式）：

| 策略 | 压缩率 | 质量分 | 适用场景 |
|------|--------|--------|----------|
| 锚定迭代摘要 | 98.6% | 3.70 | 长会话、文件追踪重要 |
| 再生式摘要 | 98.7% | 3.44 | 清晰阶段边界 |
| 不透明压缩 | 99.3% | 3.35 | 最大化节省token |

#### 4.1.2 结构化摘要模板

```yaml
# Session Summary Schema
session_summary:
  version: "1.0"

  # 会话意图 - 必须保留
  intent:
    goal: str              # 用户目标
    constraints: list[str]  # 约束条件
    success_criteria: str  # 成功标准

  # 修改的文件 - 关键信息
  artifacts:
    modified:              # 已修改
      - path: str
        change: str
        reason: str
    created:               # 新创建
      - path: str
        purpose: str
    read_only:            # 仅读取
      - path: str
        reason: str

  # 决策记录 - 不可丢失
  decisions:
    - decision: str
      rationale: str
      context: str

  # 当前状态
  state:
    progress: str          # 完成/进行中/阻塞
    blockers: list[str]
    pending_tasks: list[str]

  # 下一步 - 恢复工作用
  next_steps:
    - step: str
      depends_on: list[str]
```

#### 4.1.3 压缩触发策略

| 触发类型 | 条件 | 动作 |
|----------|------|------|
| **手动触发** | 用户执行`/compact` | 完整压缩 + 合并到现有摘要 |
| **阈值触发** | context > 80% | 增量压缩（仅压缩新增部分） |
| **定时触发** | 每N轮 | 增量压缩 |
| **事件触发** | Agent.stop() | 仅快速摘要，不触发Evolver |

#### 4.1.4 Probe-Based质量评估

压缩后通过LLM自我评估质量：

```python
@dataclass
class CompressionQualityScore:
    recall: float          # 事实保留率
    artifact: float       # 文件追踪能力
    continuity: float     # 继续工作能力
    decision: float       # 决策保留率

    @property
    def overall(self) -> float:
        return (self.recall * 0.25 +
                self.artifact * 0.30 +  # 最高权重
                self.continuity * 0.20 +
                self.decision * 0.25)
```

---

## 5. 事件驱动架构 (Claude Code模式)

### 5.1 Hooks系统设计

#### 5.1.1 可用Hooks

参考Claude Code的12个生命周期Hooks：

| Hook | 触发时机 | Harness动作 | Evolver动作 |
|------|----------|-------------|-------------|
| `on_execution_start` | Agent开始执行 | 初始化上下文 | - |
| `on_execution_end` | Agent执行完成 | 记录Trace | - |
| `on_message` | 每条消息 | 更新消息队列 | - |
| `on_tool_call` | 工具调用前 | - | - |
| `on_tool_result` | 工具调用后 | 记录结果 | - |
| `on_compact` | 上下文压缩前 | 触发压缩 | - |
| `on_compacted` | 上下文压缩后 | 保存摘要 | 触发知识蒸馏 |
| `on_error` | 错误发生 | 记录错误 | 提取失败模式 |
| `on_session_start` | 会话开始 | 加载历史摘要 | - |
| `on_session_end` | 会话结束 | 保存状态 | 触发进化 |
| `on_quota_exceeded` | 配额超限 | 暂停/降级 | - |
| `on_evolve` | 触发进化 | - | 执行Gene提取 |

### 5.2 错误恢复机制

采用**分层防御**策略：
- **瞬时错误**: 指数退避重试（最多3次）
- **永久错误**: 记录并继续执行其他hooks
- **关键错误**: 记录critical alert，阻止流程继续

---

## 6. Evolver 系统设计 (自进化)

### 6.1 六阶段进化循环

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     六阶段进化循环                                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│    ┌───────┐    ┌────────┐    ┌─────────┐    ┌─────────┐    ┌───────┐ │
│    │ Trace │───▶│Evaluate│───▶│ Distill │───▶│ Compile │───▶│ Verify │ │
│    └───────┘    └────────┘    └─────────┘    └─────────┘    └───────┘ │
│        │                                               │               │
│        │                    ┌─────────┐                 │               │
│        │                    │  Apply  │◀────────────────┘               │
│        │                    └─────────┘                                 │
│        │                          │                                     │
│        └──────────────────────────┘                                     │
│                    累积经验库                                            │
└─────────────────────────────────────────────────────────────────────────┘
```

1. **Trace**: 记录执行轨迹（工具调用、决策点、结果）
2. **Evaluate**: 评估执行质量（成功率、效率、用户满意度）
3. **Distill**: 从轨迹中提取可复用知识（语义/情景/程序记忆）
4. **Compile**: 编译优化方案（生成Gene）
5. **Verify**: 验证优化方案（测试+评估）
6. **Apply**: 应用验证通过的优化（更新Skill/Prompt/Workflow）

### 6.2 知识蒸馏 (Knowledge Distillation)

#### 6.2.1 三类记忆提取

```python
@dataclass
class KnowledgeDistillate:
    """知识蒸馏产物"""

    # 语义记忆 - 事实和偏好
    semantic: list[SemanticMemory]

    # 情景记忆 - 执行经验
    episodic: list[EpisodicMemory]

    # 程序记忆 - 行为模式
    procedural: list[ProceduralMemory]

@dataclass
class SemanticMemory:
    """语义记忆"""
    fact: str           # "用户偏好Python 3.12"
    source: str         # 来源消息ID
    confidence: float

@dataclass
class EpisodicMemory:
    """情景记忆"""
    event: str         # "技术方案评分要点分析"
    outcome: str       # "高分"
    pattern: str       # "先列评分要点再展开"
    context: str       # 上下文

@dataclass
class ProceduralMemory:
    """程序记忆"""
    rule: str          # "商务响应使用'完全响应'"
    trigger: str      # 触发条件
    result: str       # 预期结果
```

### 6.3 Gene与Capsule结构

#### 6.3.1 Gene结构

```python
@dataclass
class Gene:
    """基因 - 可移植能力单元"""

    gene_id: str
    gene_type: GeneType  # skill, prompt, workflow, tool

    # 内容
    content: str         # 优化内容
    variation: str        # 变异类型: rephrase, expand, compress, reorder

    # 来源
    source_summary: str  # 来源摘要
    source_session: str  # 来源会话

    # 评估
    confidence: float    # 置信度 0-1
    evaluation: GeneEvaluation | None = None

    # 元数据
    created_at: datetime
    version: str
```

#### 6.3.2 Capsule结构

```python
@dataclass
class Capsule:
    """胶囊 - 可导出包"""

    capsule_id: str
    version: str

    # 核心内容
    genes: list[Gene]
    signature: CapsuleSignature  # 输入输出定义

    # 元数据
    name: str
    description: str
    tags: list[str]

    # 验证
    validation_rules: list[ValidationRule]
    examples: list[Example]

    # 依赖
    dependencies: list[str]

    # 生命周期
    created_at: datetime
    updated_at: datetime
    status: CapsuleStatus  # draft, testing, active, deprecated
```

#### 6.3.3 三级Capsule存储结构

```
```
capsule-name/
├── CAPSULE.yaml        # Capsule 元信息
├── CAPSULE.md         # Level 2: 核心指令 (触发时加载)
├── GENES/             # Level 1: 多个 Gene (启动时索引)
│   ├── AGENTS/       # Agent 相关 Gene
│   │   ├── decision-bid-analysis-20260228T101000Z.yaml
│   │   └── strategy-customer-service-20260227T154500Z.yaml
│   ├── SKILLS/      # Skill 相关 Gene
│   │   ├── prompt-code-review-20260228T090000Z.yaml
│   │   └── instruction-bid-generation-20260226T120000Z.yaml
│   ├── TOOLS/        # Tool 相关 Gene
│   │   └── selection-data-analysis-20260225T143000Z.yaml
│   └── WORKFLOWS/    # Workflow 相关 Gene
│       └── orchestration-bid-pipeline-20260224T110000Z.yaml
├── META/              # Level 3: 按需加载
│   ├── validation.yaml
│   ├── examples.md
│   ├── deps.yaml
│   └── history.md
└── scripts/
    └── validate.sh
```

---

#### 6.3.4 Gene 命名规范

格式：`{type}-{theme}-{timestamp}`

示例：`prompt-bid-analysis-20260228T101000Z.yaml`

组成部分：
- type: 基因类型 (prompt, strategy, decision, instruction, selection, orchestration)
- theme: 核心主题 (3-5词, 中划线分隔)
- timestamp: ISO 8601 紧凑格式 (YYYYMMDD'T'HHMMSS'Z')


Gene 类型：
- AGENTS: decision, strategy, behavior
- SKILLS: prompt, instruction, workflow
- TOOLS: selection
- WORKFLOWS: orchestration
├── CAPSULE.yaml        # Capsule 元信息
├── CAPSULE.md         # Level 2: 核心指令 (触发时加载)
├── GENES/             # Level 1: 多个 Gene (启动时索引)
│   ├── gene-1.yaml
│   ├── gene-2.yaml
│   └── gene-N.yaml
├── META/              # Level 3: 按需加载
│   ├── validation.yaml
│   ├── examples.md
│   ├── deps.yaml
│   └── history.md
└── scripts/
    └── validate.sh

---

## 7. DataCenter 系统设计

### 7.1 定位

DataCenter 是统一的数据存储层，包含：
- **Harness**: 数据获取方式（TraceLog, Metrics, FailurePattern）
- **Memory**: 记忆层（Episodic/Semantic/Working）
- **Checkpoints**: 状态恢复

服务 Evolver Capsule 检索 + Agent 运行时按需加载

### 7.2 架构

```
┌─────────────────────────────────────────────────────────────┐
│                     DataCenter                              │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Harness (数据获取方式)                              │   │
│  │  - TraceLog: 执行轨迹记录                          │   │
│  │  - Metrics: 运行时指标                             │   │
│  │  - FailurePattern: 失败模式                        │   │
│  └─────────────────────────────────────────────────────┘   │
│                           │                                 │
│                           ▼                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Memory Layers (记忆层)                             │   │
│  │  - Episodic: 情景记忆（执行经验）                 │   │
│  │  - Semantic: 语义记忆（事实和偏好）               │   │
│  │  - Working: 工作记忆（当前状态）                   │   │
│  └─────────────────────────────────────────────────────┘   │
│                           │                                 │
│                           ▼                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Checkpoints (状态恢复)                             │   │
│  │  - Snapshot: 完整状态快照                         │   │
│  │  - Incremental: 增量检查点                        │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 7.3 存储结构 (对齐OpenCode)

```jsonl
// Entity.jsonl
{"id": "entity_1", "type": "concept", "name": "Python", "description": "...", "observations": []}
{"id": "entity_2", "type": "tool", "name": "grep", "description": "...", "observations": []}

// Relation.jsonl
{"from": "entity_1", "to": "entity_2", "relation": "uses", "context": "..."}

// Observation.jsonl
{"entity_id": "entity_1", "timestamp": "...", "content": "...", "source": "..."}
```

### 7.4 两阶段检索

1. **倒排索引**: 关键词 → 候选实体
2. **细粒度评分**: 向量相似度 + 关系权重 + 时效性

### 7.5 导入格式

- YAML/JSON文件格式
- 自动解析Entity/Relation/Observation

### 7.6 Harness 与 DataCenter 关系

| 组件 | 职责 | 输出 |
|------|------|------|
| **Harness** | 数据获取（TraceLog, Metrics） | 原始执行数据 |
| **DataCenter** | 数据存储 + 检索 | 结构化记忆 |

NR|数据流: `Harness → DataCenter → EvaluationCenter / Evolver`

---

PR|## 8. EvaluationCenter 系统设计

### 8.1 定位

评估系统的核心枢纽，支持：
- **多类型评估**: 正确性、效率、安全性、用户体验
- **多层级评估**: 单元、集成、系统、E2E
- **独立使用逻辑**: 评估功能可独立使用
- **包配置管理**: 包配置受 Package Manager 管控

### 8.2 架构

```
┌─────────────────────────────────────────────────────────────┐
SZ|│                    EvaluationCenter                           │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────┐   │
│  │  评估器注册表 (Registry)                             │   │
│  │  - BaseMetric (评估器基类)                          │   │
│  │  - 评估器发现与加载                                │   │
│  └─────────────────────────────────────────────────────┘   │
│                           │                                 │
│                           ▼                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  评估类型 (Evaluation Types)                        │   │
│  │  - Correctness: 正确性评估                         │   │
│  │  - Efficiency: 效率评估                            │   │
│  │  - Safety: 安全性评估                              │   │
│  │  - UX: 用户体验评估                               │   │
│  └─────────────────────────────────────────────────────┘   │
│                           │                                 │
│                           ▼                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  评估层级 (Evaluation Levels)                       │   │
│  │  - Unit: 单元测试级                               │   │
│  │  - Integration: 集成级                           │   │
│  │  - System: 系统级                                 │   │
│  │  - E2E: 端到端级                                 │   │
│  └─────────────────────────────────────────────────────┘   │
│                           │                                 │
│                           ▼                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  评估注入 (Evaluation Injection)                    │   │
│  │  - 按场景选择评估器                               │   │
│  │  - 动态评估策略                                   │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 8.3 与其他系统关系

| 系统 | 关系 | 数据流 |
|------|------|--------|
HV|| **DataCenter** | 数据源 | Harness 收集的执行数据 → EvaluationCenter |
| **Evolver** | 评估结果消费者 | 评估分数 → Evolver 进化决策 |
| **Package Manager** | 包配置管理 | 评估包版本/依赖管理 |

### 8.4 评估器接口

```python
@dataclass
class EvaluationResult:
    score: float              # 评分 0-1
    metrics: dict            # 详细指标
    feedback: str            # 评估反馈
    timestamp: datetime

class BaseMetric(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def evaluation_type(self) -> EvaluationType:
        pass

    @property
    @abstractmethod
    def evaluation_level(self) -> EvaluationLevel:
        pass

    @abstractmethod
    async def evaluate(self, context: EvaluationContext) -> EvaluationResult:
        pass
```

---

## 9. Package Manager 设计
---

## 8. Package Manager 设计

### 8.1 包类型

| 类型 | 说明 | 示例 |
|------|------|------|
| **skill** | Skill 包 | `@legal/contract-skills` |
| **dataset** | 数据集包 | `@medical/diagnosis-dataset` |
| **evaluation** | 评估规则包 | `@bid/compliance-rules` |
| **mcp** | MCP 服务包 | `@github/mcp-server` |
| **capsule** | Capsule 包 | `@patterns/code-review-capsule` |

### 8.2 依赖解析

精确求解（参考Cargo SAT）：
- 版本约束：精确版本、范围、兼容
- 冲突检测：循环依赖、版本冲突
- Lock文件：锁定精确版本

### 8.3 版本策略（增强版 Cargo）

| 表达式 | 含义 | 示例 |
|--------|------|------|
| `^` | 兼容版本 | `^1.2.3` → `>=1.2.3 <2.0.0` |
| `~` | 补丁兼容 | `~1.2.3` → `>=1.2.3 <1.3.0` |
| `=` | 精确版本 | `=1.2.3` |
| `>` `<` `>=` `<=` | 范围比较 | `>=1.0 <2.0` |
| `\|\|` | 或组合 | `^1.0 \|\| ^2.0` |

### 8.4 Source 系统

```yaml
# .mightyoung/sources.yaml
sources:
  - name: "my-market"
    type: "local"
    path: "./my-market"
  - name: "github-skills"
    type: "github"
    repo: "owner/repo"
    auth:
      type: "token"
      env: "GITHUB_TOKEN"
```

### 8.5 存储结构

```
项目目录/
├── .mightyoung/
│   ├── sources.yaml           # Source 配置
│   ├── packages/              # 已安装包（只读）
│   ├── cache/
│   └── config.yaml
└── agents/
    └── <agent>/
        ├── mightyoung.yaml   # Agent 定义
        └── lock.yaml        # Agent 级锁定
```

---

## 9. Package Manager 与 Evolver 关系设计

### 9.1 冲突问题

| 组件 | 行为 | 冲突点 |
|------|------|--------|
| **Package Manager** | lock.yaml 锁定版本，从 .mightyoung/packages/ 加载 | 只读 |
| **Evolver** | 运行时改进 Skill，内存覆盖 | 可写，无持久化 |

### 9.2 解决方案：分层存储 + 加载顺序

```
加载顺序（优先级从高到低）：

1. agents/my-agent/evolved/   # 进化后的 Skill（Agent级）
2. .mightyoung/evolved/     # 进化后的 Skill（全局）
3. .mightyoung/packages/    # 安装的原始包（只读）
```

### 9.3 目录结构

```
agents/my-agent/
├── mightyoung.yaml           # Agent 定义
├── lock.yaml                # Agent 级锁定
├── evolved/                 # 进化后的 Skill
│   └── @org/
│       └── skill-a/
│           └── skill.md
└── merge_history/          # 合并历史
    └── skill-a/
        └── 2026-02-28_merge.yaml
```

### 9.4 合并策略

当原始 Skill 升级时，检测进化版本并进行三路合并：

| 策略 | 说明 | 适用场景 |
|------|------|----------|
| **自动合并** | 无冲突时自动合并 | 简单改动 |
| **LLM 合并** | AI 智能解决冲突 | 复杂语义修改 |
| **手动合并** | 用户介入解决 | 高风险冲突 |

### 9.5 用户交互

```
检测到 Skill "@org/skill-a" 有新版本 v1.2.0

当前使用：进化版 v1.1.0 (本地修改)

请选择：
[A] 自动合并 - 升级版新功能 + 进化版修改
[B] 保留进化版 - 忽略升级
[C] 覆盖为升级版 - 丢弃进化版
[D] 手动查看差异
```

### 9.6 核心原则

| 原则 | 说明 |
|------|------|
| **解耦** | Package 是独立实体，Agent 按需引用 |
| **共享** | Package 可被多个 Agent 共享 |
| **锁定** | lock.yaml 锁定原始版本 |
| **进化优先** | 同名包优先加载进化版本 |
| **自动检查** | 安装/升级时自动检查兼容性 |
| **多版本** | 支持同一 Package 不同版本共存 |

PQ|### 9.7 Package Manager 与 EvaluationCenter 关系

| 组件 | 职责 | 关系 |
|------|------|------|
| **Package Manager** | 包版本/依赖管理 | 管控 Evaluation 包的配置 |
TW|| **EvaluationCenter** | 评估执行逻辑 | 使用逻辑独立于 PM |

**核心原则**：
KT|- EvaluationCenter 的**使用逻辑独立**于 Package Manager
- Evaluation 包的**版本和依赖**由 Package Manager 管控
NV|- 评估器注册在 EvaluationCenter 中，加载的评估包由 PM 管理

---

## 10. 目录结构

---

## 10. 目录结构

### 10.1 项目结构

```
mightyoung/
├── .mightyoung/                   # 本地包管理
│   ├── sources.yaml              # Source 配置
│   ├── packages/                 # 已安装包（只读）
│   ├── evolved/                  # 进化后的包（全局）
│   ├── cache/
│   ├── locks/
│   └── config.yaml
├── src/                          # 核心代码
│   ├── core/                     # 核心引擎
│   ├── agents/                   # Agent 定义
│   ├── skills/                   # Skill 系统
│   ├── datacenter/               # DataCenter 系统 (含 Harness)
ZX|│   ├── evaluation/               # EvaluationCenter 系统
│   ├── growth/                   # Evolver自进化系统
│   └── plugins/                  # 插件系统 (含 Package Manager)
├── skills/                       # Skill定义
├── packages/                     # Package定义
├── config/                       # 配置文件
├── tests/                        # 测试
├── docs/                         # 文档
│   └── design/                   # 设计文档
└── mightyoung.yaml               # 项目配置
```

---

## 11. 实施计划

### 11.1 阶段划分

| 阶段 | 任务 | 预计工作量 |
|------|------|-------------|
| **Phase 1** | Package Manager 基础实现 | 2天 |
| **Phase 2** | DataCenter 系统实现 (含 Harness) | 3天 |
SS|| **Phase 3** | EvaluationCenter 系统实现 | 2天 |
| **Phase 4** | Hooks系统基础实现 | 2天 |
| **Phase 5** | Evolver蒸馏实现 | 3天 |
| **Phase 6** | 集成测试 | 2天 |
| **Phase 7** | 优化和文档 | 1天 |

### 11.2 依赖关系

```
Phase 1 (Package)
    │
    ├─▶ Phase 2 (DataCenter + Harness)
    │         │
    JX|    │         ├─▶ Phase 3 (EvaluationCenter)
    │         │         │
    │         │         ├─▶ Phase 4 (Hooks)
    │         │         │         │
    │         │         │         ├─▶ Phase 6 (集成测试)
    │         │         │         │
    │         │         │         └─▶ Phase 5 (Evolver蒸馏)
    │         │         │                   │
    │         │         │                   └─▶ Phase 6 (集成测试)
    │         │         │
    │         │         └─▶ Phase 6 (集成测试)
    │         │
    └───────────────────────────▶ Phase 7 (优化)
```

---

## 12. 关键设计决策

### 12.1 设计原则

| 决策点 | 方案 | 理由 |
|--------|------|------|
| **零外部依赖** | Core = SQLite + 内存 | 开箱即用、可移植 |
| **压缩策略** | 锚定迭代摘要 | 质量分最高(3.70) |
| **事件架构** | Claude Code Hooks | 简单、经过验证 |
| **错误恢复** | 分层防御 | 平衡可靠性和复杂度 |
| **蒸馏触发** | on_compacted事件 | 压缩后数据最完整 |
| **进化维度** | Skill+Prompt+Workflow | Tool后续支持 |
| **DataCenter存储** | JSONL (对齐OpenCode) | 简单、可检索 |
| **Harness集成** | 作为 DataCenter 的一部分 | 统一数据流 |
SN|| **EvaluationCenter** | 独立使用逻辑 + PM 管控配置 | 解耦评估逻辑与包管理 |
| **包管理** | 本地优先 + Market | 离线可用 + 生态扩展 |
| **进化存储** | Agent 级 | 隔离性好 |
| **合并策略** | 三路合并 + LLM | 智能解决冲突 |

### 11.2 依赖关系

```
Phase 1 (Package)
    │
    ├─▶ Phase 2 (Dataset)
    │         │
    │         ├─▶ Phase 3 (Hooks)
    │         │         │
    │         │         ├─▶ Phase 4 (Harness压缩)
    │         │         │         │
    │         │         │         └─▶ Phase 6 (集成测试)
    │         │         │
    │         │         └─▶ Phase 5 (Evolver蒸馏)
    │         │                   │
    │         │                   └─▶ Phase 6 (集成测试)
    │         │
    └───────────────────────────▶ Phase 7 (优化)
```

---

## 12. 关键设计决策

### 12.1 设计原则

| 决策点 | 方案 | 理由 |
|--------|------|------|
| **零外部依赖** | Core = SQLite + 内存 | 开箱即用、可移植 |
| **压缩策略** | 锚定迭代摘要 | 质量分最高(3.70) |
| **事件架构** | Claude Code Hooks | 简单、经过验证 |
| **错误恢复** | 分层防御 | 平衡可靠性和复杂度 |
| **蒸馏触发** | on_compacted事件 | 压缩后数据最完整 |
| **进化维度** | Skill+Prompt+Workflow | Tool后续支持 |
| **Dataset存储** | JSONL (对齐OpenCode) | 简单、可检索 |
| **包管理** | 本地优先 + Market | 离线可用 + 生态扩展 |
| **进化存储** | Agent 级 | 隔离性好 |
| **合并策略** | 三路合并 + LLM | 智能解决冲突 |

---

## 13. 参考实现

- **OpenCode**: `~/.config/opencode/skills/context-compression/SKILL.md`
- **Claude Code**: 三层压缩 + 12 Hooks
- **EvoMap**: 进化算法框架
- **AgentEvolver**: ModelScope AgentEvolver
- **ReMe**: AgentScope记忆管理框架
- **LangMem**: LangChain记忆系统
- **DSPy**: Stanford程序化提示工程
- **Cargo**: SAT 依赖解析
- **Claude Code Market**: Source 结构

---

## 附录：设计版本历史

```
v1.0 (2026-02-28): 初始设计
  - Evolver六阶段循环
  - 锚定迭代摘要
  - Claude Code Hooks模式
  - Dataset两阶段检索
  - Package Manager设计

HN|v1.3 (本文档): DataCenter + EvaluationCenter 架构更新
  - DataSet 重新定位为 DataCenter
  - Harness 纳入 DataCenter 作为数据获取方式
  KK|  - 新增 EvaluationCenter 系统设计
  QT|  - 更新支柱架构: Agent / DataCenter / EvaluationCenter
  YM|  - 新增 Package Manager 与 EvaluationCenter 关系
  - 更新目录结构和实施计划

v1.2: Capsule/Gene 设计更新
  - 参照 OpenClaw GEP 协议
  - 新增冲突解决策略 (auto/llm/manual)
  - 新增动态进化频率设计
  - 新增验证命令白名单

v1.1: 集成设计更新
  - 整合四大核心系统
  - 更新目录结构
  - 完善实施计划
  - 新增 Package Manager 与 Evolver 关系设计
  - 新增 Skill 进化版本存储与合并策略
```

---

*本文档基于 ARCHITECTURE.md v1.3*

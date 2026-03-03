# OpenYoung 完整实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 构建 OpenYoung 多智能体bid生成平台，基于OpenCode架构，具备自进化能力

**Architecture:** OpenYoung采用三层架构：合作层(通用Skill/MCP)→通用层(Agent范式)→价值提升层(行业Agent)。核心零外部依赖原则。

**Tech Stack:** Python 3.10+, Pydantic v2, asyncio, type hints

---

## 设计文档清单

| 文档 | 内容 | 行数 |
|------|------|------|
| young-agent-core.md | 核心架构（类型、Agent、SubAgent、权限、配置） | 611 |
| young-agent-flow.md | Flow Skill 集成 | 284 |
| young-agent-prompt.md | 提示词模板系统 | 330 |
| young-agent-memory.md | 记忆系统（Checkpoint、Auto Memory、Skills） | 563 |
| young-agent-integration.md | 外部系统集成 | 676 |
| package-manager-design.md | 包管理系统 | 744 |
| datacenter-design.md | 数据中心（Harness、三层记忆） | 674 |
| evaluation-hub-design.md | 评估中心 | 1037 |
| evolver-design.md | 自进化系统（Gene、Capsule） | 666 |
| unified-skill-retriever-design.md | 统一技能检索 | 627 |
| integrat-design.md | 整体集成架构（三层设计） | 999 |

---

## Phase 1: 核心类型系统 (Task 1.1-1.2)

### Task 1.1: 枚举和配置类型
**Files:** src/core/types.py, tests/core/test_types.py

### Task 1.2: 消息和任务类型
**Files:** src/core/types.py (追加), tests/core/test_messages.py

---

## Phase 2: Agent 系统 (Task 2.1-2.3)

### Task 2.1: YoungAgent 主类
**Files:** src/agents/young_agent.py, tests/agents/test_young_agent.py

### Task 2.2: TaskDispatcher (SubAgent系统)
**Files:** src/agents/dispatcher.py, tests/agents/test_dispatcher.py

### Task 2.3: PermissionEvaluator (ask/allow/deny)
**Files:** src/agents/permission.py, tests/agents/test_permission.py

---

## Phase 3: Flow Skill 系统 (Task 3.1-3.2)

### Task 3.1: FlowSkill抽象基类 + SequentialFlow
**Files:** src/flow/base.py, src/flow/sequential.py, tests/flow/test_base.py

### Task 3.2: ParallelFlow, ConditionalFlow, LoopFlow
**Files:** src/flow/parallel.py, src/flow/conditional.py, src/flow/loop.py

---

## Phase 4: 提示词模板系统 (Task 4.1)

### Task 4.1: PromptTemplate & Registry
**Files:** src/prompts/templates.py, src/prompts/loader.py, tests/prompts/test_templates.py

---

## Phase 5: 记忆系统 (Task 5.1-5.2)

### Task 5.1: CheckpointManager
**Files:** src/memory/checkpoint.py, tests/memory/test_checkpoint.py

### Task 5.2: AutoMemory (三层记忆)
**Files:** src/memory/auto_memory.py, tests/memory/test_auto_memory.py

---

## Phase 6: Package Manager (Task 6.1)

### Task 6.1: Package模型 & Loader
**Files:** src/packages/models.py, src/packages/loader.py, tests/packages/test_loader.py

---

## Phase 7: DataCenter (Task 7.1-7.2)

### Task 7.1: TraceCollector
**Files:** src/datacenter/trace.py, tests/datacenter/test_trace.py

### Task 7.2: BudgetController & PatternDetector
**Files:** src/datacenter/budget.py, src/datacenter/patterns.py

---

## Phase 8: Evolver 系统 (Task 8.1-8.2)

### Task 8.1: Gene, Capsule, EvolutionEvent, Personality模型
**Files:** src/evolver/models.py, tests/evolver/test_models.py

### Task 8.2: GeneLoader (YAML)
**Files:** src/evolver/loader.py, tests/evolver/test_loader.py

---

## Phase 9: EvaluationHub (Task 9.1)

### Task 9.1: Evaluation Package Registry
**Files:** src/evaluation/hub.py, tests/evaluation/test_hub.py

---

## Phase 10: Unified Skill Retriever (Task 10.1)

### Task 10.1: 双轨检索 (Package + Semantic)
**Files:** src/retriever/unified.py, tests/retriever/test_unified.py

---

## Phase 11: 集成与配置 (Task 11.1)

### Task 11.1: 配置文件加载 (mightyoung.yaml, .env)
**Files:** src/config/loader.py, tests/config/test_loader.py

---

## 代码复用策略

| 组件 | 复用来源 |
|------|----------|
| Agent类型 | OpenCode (TypeScript→Python) |
| Permission | OpenCode permission.ts |
| Checkpoint | Claude Code设计 |
| Gene/Capsule | OpenClaw GEP YAML |
| Package Loader | Cargo/npm模式 |
| Prompt Templates | Windsurf/Manus/Devin结构 |

---

## 实施顺序建议

1. **Phase 1** (核心类型) - 基础，必须先完成
2. **Phase 2** (Agent系统) - 核心业务逻辑
3. **Phase 5** (记忆系统) - Agent依赖
4. **Phase 3** (Flow) - 可选，后完成
5. **Phase 4** (提示词) - 可选，后完成
6. **Phase 6-11** (扩展系统) - 按需实现

---

**计划保存至:** docs/plans/2026-03-02-openyoung-complete-implementation.md

**两种执行选项:**
1. **子代理驱动（本会话）** - 每个任务分配新子代理，任务间审查
2. **并行会话（独立）** - 使用 executing-plans 技能打开新会话，分批执行

**您选择哪种方式？**

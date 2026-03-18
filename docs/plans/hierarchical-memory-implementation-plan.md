# 分层记忆系统实现计划

**目标**: 实现混合记忆系统 (Working + Semantic + Checkpoint)
**基于**: OpenViking 分层思想 + PageIndex LLM 推理 + EventBus 事件驱动

---

## 架构概览

```
┌─────────────────────────────────────────────────────────────┐
│                    Hybrid Memory System                      │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐  │
│  │   Working    │    │  Semantic   │    │  Checkpoint │  │
│  │  (L0)       │    │   (L2)     │    │  (State)    │  │
│  ├─────────────┤    ├─────────────┤    ├─────────────┤  │
│  │ 当前任务状态  │    │ LLM 推理   │    │ Agent 状态  │  │
│  │ 内存存储     │    │ 知识检索   │    │ 快照恢复    │  │
│  │ ~10KB       │    │ ~100KB      │    │ ~50KB       │  │
│  └─────────────┘    └─────────────┘    └─────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 分步计划

### Phase 1: Working Memory (L0) - 当前任务状态 ✅

**目标**: 存储和管理当前任务的运行时状态

**时间**: 1-2 天

| 任务 | 文件 | 说明 |
|------|------|------|
| P1.1 设计 WorkingMemory 接口 | `src/core/memory/working.py` | 当前任务上下文存储 |
| P1.2 实现内存存储 | 同上 | 使用 dict + 持久化备份 |
| P1.3 集成 EventBus | 同上 | 监听任务开始/切换事件 |
| P1.4 单元测试 | `tests/core/test_working_memory.py` | 基础 CRUD 测试 |

**验收标准**:
- [x] WorkingMemory 可存储/读取任务上下文
- [x] 任务切换时自动保存/恢复
- [x] 与 EventBus 集成 (通过事件驱动)

**已创建文件**:
- `src/core/memory/__init__.py`
- `src/core/memory/working.py`
- `tests/core/test_working_memory.py` (14 tests passed)

---

### Phase 2: Checkpoint 增强 (State) - Agent 状态快照 ✅

**目标**: 增强现有的 CheckpointManager，支持完整状态恢复

**时间**: 1-2 天

**已有**: `src/core/agent_checkpoint.py` (PostgreSQL)

| 任务 | 文件 | 说明 |
|------|------|------|
| P2.1 扩展 Checkpoint 字段 | `src/core/agent_checkpoint.py` | 添加 messages, tools_used 等 |
| P2.2 实现状态序列化 | 同上 | 完整状态 → JSONB |
| P2.3 集成 LangGraph State | 同上 | 与 langgraph_state.py 对接 |
| P2.4 集成测试 | `tests/core/test_checkpoint.py` | 保存/恢复流程 |

**验收标准**:
- [x] Checkpoint 保存完整 Agent 状态
- [x] 可从任意 Checkpoint 恢复
- [x] 与 LangGraph State 兼容

**已创建文件**:
- `src/core/memory/checkpoint_integration.py` - Checkpoint/LangGraph 集成
- `tests/core/test_checkpoint_integration.py` (8 tests passed)

---

### Phase 3: Semantic Memory (L2) - LLM 推理知识检索

**目标**: 实现基于 LLM 推理的知识检索 (无向量方案)

**时间**: 2-3 天

**参考**: PageIndex 思路 - 用 LLM 理解查询意图

| 任务 | 文件 | 说明 |
|------|------|------|
| P3.1 设计 SemanticMemory 接口 | `src/core/memory/semantic.py` | 知识存储抽象 |
| P3.2 实现 LLM 推理检索 | 同上 | 构建 Prompt 让 LLM 推理相关知识 |
| P3.3 知识存储层 | 同上 | PostgreSQL JSONB 存储 |
| P3.4 集成 LLM Provider | 同上 | 复用现有 llm provider |
| P3.5 单元测试 | `tests/core/test_semantic_memory.py` | 检索准确性测试 |

**验收标准**:
- [x] SemanticMemory 存储知识条目
- [x] LLM 推理检索相关知识
- [x] 无需向量数据库

**已创建文件**:
- `src/core/memory/semantic.py` - SemanticMemory 实现
- `tests/core/test_semantic_memory.py` (12 tests passed)

---

### Phase 4: Memory Facade - 统一入口 ✅

**目标**: 提供统一的 Memory 访问接口

**时间**: 1 天

| 任务 | 文件 | 说明 |
|------|------|------|
| P4.1 设计 MemoryFacade | `src/core/memory/facade.py` | 统一入口 |
| P4.2 实现 retrieve() 方法 | 同上 | 自动路由到对应层 |
| P4.3 实现 store() 方法 | 同上 | 自动选择存储层 |
| P4.4 与 YoungAgent 集成 | `src/agents/young_agent.py` | 替换现有 memory |

**验收标准**:
- [x] 统一 API: memory.retrieve(query)
- [x] 自动分层路由
- [ ] 替换 YoungAgent 旧 memory (可选)

**已创建文件**:
- `src/core/memory/facade.py` - MemoryFacade 实现
- `tests/core/test_memory_facade.py` (13 tests passed)

---

### Phase 5: 事件驱动集成

**目标**: 用 EventBus 驱动记忆系统

**时间**: 1-2 天

| 任务 | 文件 | 说明 |
|------|------|------|
| P5.1 注册 Memory 事件 | `src/core/memory/events.py` | 记忆相关事件类型 |
| P5.2 监听任务事件 | `src/core/memory/handlers.py` | TASK_STARTED 等 |
| P5.3 自动保存 Checkpoint | 同上 | 任务切换时自动 |
| P5.4 集成测试 | `tests/core/test_memory_integration.py` | 端到端测试 |

**验收标准**:
- [x] EventBus 自动触发记忆操作
- [x] 任务切换自动保存 Checkpoint
- [x] 完整事件流程测试通过

---

## 实现顺序优先级

```
P1 (Working) → P2 (Checkpoint) → P3 (Semantic) → P4 (Facade) → P5 (集成)
     ↓            ↓              ↓            ↓            ↓
  独立可测试  与现有集成   可选(成本高)  统一API    最终集成
```

---

## 依赖关系

```
Phase 1 (Working)      ← 无依赖，独立实现
    ↓
Phase 2 (Checkpoint)  ← 依赖已有 agent_checkpoint.py
    ↓
Phase 3 (Semantic)    ← 依赖 LLM Provider (已有)
    ↓
Phase 4 (Facade)      ← 依赖 P1, P2, P3
    ↓
Phase 5 (集成)        ← 依赖 P4 + EventBus
```

---

## 文件清单

| 文件 | 状态 |
|------|------|
| `src/core/memory/__init__.py` | 新建 |
| `src/core/memory/working.py` | 新建 |
| `src/core/memory/semantic.py` | 新建 |
| `src/core/memory/events.py` | 新建 |
| `src/core/memory/handlers.py` | 新建 |
| `tests/core/test_working_memory.py` | 新建 |
| `tests/core/test_semantic_memory.py` | 新建 |
| `tests/core/test_checkpoint.py` | 新建 |
| `tests/core/test_memory_integration.py` | 新建 |

---

## 风险与缓解

| 风险 | 缓解措施 |
|------|----------|
| LLM 推理成本高 | 限制检索条数，加结果缓存 |
| 状态膨胀 | 定期清理 Checkpoint，设置 TTL |
| 复杂度高 | MVP 先只做 P1 + P2 |

---

## 验收总览

| Phase | 验收条件 |
|-------|----------|
| Phase 1 | WorkingMemory 独立可用 |
| Phase 2 | Checkpoint 完整状态保存/恢复 |
| Phase 3 | LLM 推理检索准确可用 |
| Phase 4 | 统一 API 上线 |
| Phase 5 | EventBus 自动化集成完成 |

---

**最后更新**: 2026-03-17 (全部 Phase 完成)

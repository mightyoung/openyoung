# OpenYoung 实施改进计划

> 日期: 2026-03-16
> 目标: 根据8个已批准的技术决策实施改进

---

## 目标概述

基于以下已批准的技术决策，创建分阶段实施计划：

| # | 决策 | 文档 |
|---|------|------|
| 1 | DAG任务调度 - 智能失败传播DAG | `dag-scheduling-decision.md` |
| 2 | Harness驱动 - Harness+RalphLoop | `harness-engine-decision.md` |
| 3 | Agent元数据 - 导入时提取 | `agent-metadata-decision.md` |
| 4 | 错误处理 - 分层异常架构 | `exception-hierarchy-decision.md` |
| 5 | 配置管理 - 分层配置 | `layered-config-decision.md` |
| 6 | 接口抽象 - 核心抽象 | `core-abstraction-decision.md` |
| 7 | 注册模式 - 抽象基类 | `registry-abstraction-decision.md` |
| 8 | Rust Sandbox - FFI桥接(PyO3) | `rust-sandbox-ffi-decision.md` |

---

## 项目现状分析

### 当前目录结构
```
src/
├── agents/          # Agent系统
├── api/            # API服务
├── cli/            # CLI入口 (2339行 - 需拆分)
├── config/         # 配置
├── core/           # 核心模块
├── datacenter/     # 数据存储
├── evaluation/      # 评估系统
├── harness/        # Harness引擎
├── hub/            # Hub模块
├── llm/            # LLM客户端
├── memory/         # 向量存储
├── package_manager/# 包管理
├── runtime/        # 运行时/沙箱
└── skills/         # 技能系统
```

### 关键问题
- `cli/main.py` - 2339行，违反500行原则
- `agents/young_agent.py` - 1436行，需拆分
- 多个模块职责重叠
- 缺乏统一错误处理

---

## 实施阶段

### Phase 1: 基础设施 (优先级最高)

**目标**: 建立核心基础设施，为后续改进提供基础

| 任务 | 文件 | 描述 | 依赖 |
|------|------|------|------|
| 1.1 | `src/core/exceptions.py` | 定义异常层次结构 | 无 |
| 1.2 | `src/core/interfaces/*.py` | 定义核心接口(Protocol) | 无 |
| 1.3 | `src/core/di.py` | 依赖注入容器 | 1.2 |
| 1.4 | `src/core/registry/base.py` | 抽象注册表基类 | 无 |
| 1.5 | `src/config/models.py` | 配置模型(Pydantic) | 无 |
| 1.6 | `src/config/loader.py` | 分层配置加载器 | 1.5 |

**预计工作量**: 2周

---

### Phase 2: 核心执行引擎

**目标**: 实现DAG调度和Harness引擎

| 任务 | 文件 | 描述 | 依赖 |
|------|------|------|------|
| 2.1 | `src/agents/scheduling/dag_scheduler.py` | DAG调度器 | 1.1, 1.2 |
| 2.2 | `src/agents/scheduling/failure_propagator.py` | 失败传播器 | 2.1 |
| 2.3 | `src/agents/scheduling/retry_policy.py` | 重试策略 | 2.1 |
| 2.4 | `src/agents/harness/engine.py` | Harness引擎 | 2.1, 2.2 |
| 2.5 | `src/agents/harness/phases.py` | 执行阶段管理 | 2.4 |
| 2.6 | `src/agents/harness/feedback.py` | 反馈循环 | 2.4, 2.5 |

**预计工作量**: 3周

---

### Phase 3: Agent元数据系统

**目标**: 实现Agent元数据提取和渐进披露

| 任务 | 文件 | 描述 | 依赖 |
|------|------|------|------|
| 3.1 | `src/agents/metadata/schema.py` | 元数据Schema | 无 |
| 3.2 | `src/agents/metadata/extractor.py` | GitHub提取器 | 1.1 |
| 3.3 | `src/agents/metadata/enricher.py` | LLM丰富器 | 3.1 |
| 3.4 | `src/agents/metadata/loader.py` | 渐进加载器 | 3.1, 3.2 |
| 3.5 | `src/agents/metadata/cache.py` | 缓存层 | 3.4 |
| 3.6 | `src/agents/matching/task_matcher.py` | 任务匹配器 | 3.4 |

**预计工作量**: 2周

---

### Phase 4: Rust Sandbox集成

**目标**: 通过PyO3实现Rust沙箱深度集成

| 任务 | 文件 | 描述 | 依赖 |
|------|------|------|------|
| 4.1 | `rust/ironclaw-sandbox/src/lib.rs` | Rust核心实现 | 无 |
| 4.2 | `rust/ironclaw-sandbox/src/bindings.rs` | PyO3绑定 | 4.1 |
| 4.3 | `src/runtime/sandbox/rust_wrapper.py` | Python包装 | 4.2 |
| 4.4 | `rust/ironclaw-sandbox/Cargo.toml` | 构建配置 | 4.1 |
| 4.5 | `tests/test_rust_sandbox.py` | 集成测试 | 4.3 |

**预计工作量**: 2周

---

### Phase 5: 重构现有代码

**目标**: 将现有代码迁移到新架构

| 任务 | 文件 | 描述 | 依赖 |
|------|------|------|------|
| 5.1 | `src/cli/main.py` | CLI拆分 | 1.3, 1.5 |
| 5.2 | `src/agents/young_agent.py` | Agent拆分 | 1.1-1.6, 2.x, 3.x |
| 5.3 | `src/package_manager/registry.py` | 注册表迁移 | 1.4 |
| 5.4 | `src/hub/registry/` | Hub注册表合并 | 1.4, 5.3 |
| 5.5 | `src/api/middleware.py` | 全局异常处理 | 1.1 |

**预计工作量**: 4周

---

## 任务依赖图

```
Phase 1 (基础)
    │
    ├── 1.1 exceptions.py ──────┐
    ├── 1.2 interfaces.py ──────┤
    ├── 1.4 registry.py ────────┤
    └── 1.5 config.py ──────────┘
            │
            ▼
Phase 2 (核心引擎)              Phase 3 (元数据)
    │                                │
    ├── 2.1 DAG ────────────────────┼──► 3.1 schema.py
    │    │                          │         │
    │    ├── 2.2 failure           │         ├── 3.2 extractor.py
    │    │    └── 2.3 retry       │         │    │
    │    │                         │         │    ├── 3.3 enricher.py
    │    │                         │         │    │    │
    │    └── 2.4 harness ◄────────┤         │    └── 3.4 loader.py
    │         │                    │         │         │
    │         ├── 2.5 phases ◄────┤         │    3.5 cache.py
    │         │                    │         │         │
    │         └── 2.6 feedback ◄───┘         │    3.6 matcher.py
    │                                      │         │
    └──────────────────────────────────────┘         │
            │                                            │
            ▼                                            ▼
Phase 5 (重构)                           Phase 4 (Rust)
    │                                        │
    ├── 5.1 CLI拆分 ◄──────────────────────┼──► 4.1 Rust核心
    │    │                                    │         │
    ├── 5.2 Agent拆分 ◄─────────────────────┤         ├── 4.2 PyO3
    │    │                                    │         │    │
    ├── 5.3 Registry迁移 ◄───────────────────┤         │    └── 4.3 wrapper
    │    │                                    │         │         │
    ├── 5.4 Hub合并 ◄────────────────────────┤         │    4.4 Cargo.toml
    │    │                                    │         │         │
    └── 5.5 异常处理 ◄───────────────────────┘         │    4.5 tests
                                                        │         │
                                                        └─────────┘
```

---

## 优先级排序

### 优先级1: 必须实施 (MVP)

| 任务 | 原因 |
|------|------|
| 1.1 异常层次 | 所有模块依赖 |
| 1.2 核心接口 | 其他抽象依赖 |
| 2.1 DAG调度 | 核心执行能力 |
| 2.4 Harness引擎 | 主要执行流程 |
| 1.5 配置模型 | 项目基础配置 |

### 优先级2: 重要功能

| 任务 | 原因 |
|------|------|
| 1.3 依赖注入 | 解耦核心 |
| 1.4 注册表基类 | 统一注册模式 |
| 3.1 元数据Schema | Agent管理基础 |
| 3.2 元数据提取 | Import必需 |

### 优先级3: 增强功能

| 任务 | 原因 |
|------|------|
| 4.x Rust集成 | 性能优化 |
| 5.x 重构 | 技术债务 |

---

## 里程碑

| 周次 | 里程碑 | 交付物 |
|------|---------|--------|
| W1-2 | Phase 1完成 | 异常、接口、注册表、配置基础 |
| W3-5 | Phase 2完成 | DAG调度、Harness引擎可用 |
| W6-7 | Phase 3完成 | Agent元数据系统完成 |
| W8-9 | Phase 4完成 | Rust沙箱集成完成 |
| W10-13 | Phase 5完成 | 代码重构完成 |

---

## 风险与缓解

| 风险 | 影响 | 缓解 |
|------|------|------|
| 破坏现有功能 | 系统不稳定 | 渐进迁移、保留后备 |
| 开发周期过长 | 需求变更 | 敏捷迭代、里程碑验证 |
| 人员变动 | 知识丢失 | 文档完整、代码注释 |

---

## 下一步行动

1. **立即开始**: Phase 1 任务 1.1 - 定义异常层次结构
2. **同步进行**: 审查现有代码，准备迁移计划
3. **每周回顾**: 检查进度，调整计划

---

*计划创建时间: 2026-03-16*
*基于8个已批准的技术决策*

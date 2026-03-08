# OpenYoung 执行计划

> 基于 /docs/design 设计文档 + 代码现状评估

## 项目概述

OpenYoung 是一个 AI Agent 平台，参考 OpenCode、Claude Code、Codex 架构。

**当前完成度**: ~35%

**目标**: 完善各模块实现，达到生产可用状态

---

## 阶段 1: Package Manager 核心 (优先级: P0)

### 1.1 目标
实现完整的包管理系统，支持：
- 持久化存储
- LLM Provider 管理
- 依赖解析

### 1.2 设计来源
- `/docs/design/package-manager-design.md`
- 参考: npm, Cargo, uv

### 1.3 实现任务

| 任务 | 描述 | 优先级 |
|------|------|--------|
| PM-01 | 创建持久化存储结构 (.mightyoung/) | P0 |
| PM-02 | 实现 Registry 持久化 (registry.json) | P0 |
| PM-03 | 实现 LLM Provider 包管理 | P0 |
| PM-04 | 实现 lock.yaml 生成/解析 | P1 |
| PM-05 | 实现 Source 配置 (sources.yaml) | P2 |
| PM-06 | 实现 CLI llm 命令集 | P0 |

### 1.4 引用代码
- 持久化: 参考 OpenCode `json-migration.ts`
- CLI: 参考 OpenCode CLI 命令结构

### 1.5 产出
```
src/package_manager/
├── __init__.py
├── manager.py          # 增强现有实现
├── storage.py          # 新增: 持久化层
├── provider.py        # 新增: LLM Provider 管理
├── lock.py            # 新增: lock.yaml 处理
└── registry.py        # 新增: 包注册表
```

---

## 阶段 2: Skill Loader 渐进式披露 (优先级: P0)

### 2.1 目标
实现 Skill 渐进式加载系统：
- 元数据索引
- 按需加载完整内容
- 统一检索

### 2.2 设计来源
- `/docs/design/young-agent-memory.md` Section 3

### 2.3 实现任务

| 任务 | 描述 | 优先级 |
|------|------|--------|
| SL-01 | 实现 SkillMetadata 数据结构 | P0 |
| SL-02 | 实现元数据索引构建 | P0 |
| SL-03 | 实现按需加载 (load_skill) | P0 |
| SL-04 | 实现 Skill 卸载 (unload_skill) | P1 |
| SL-05 | 集成 Package Manager 加载 | P0 |
| SL-06 | 实现统一检索接口 | P1 |

### 2.4 引用代码
- 渐进式披露: 参考 Codex 模式
- Skill 格式: 参考 Anthropic SKILL.md 标准

### 2.5 产出
```
src/skills/
├── __init__.py
├── loader.py           # 新增: SkillLoader
├── metadata.py        # 新增: 元数据结构
├── registry.py        # 新增: Skill 注册表
└── retriever.py       # 新增: 统一检索
```

---

## 阶段 3: YoungAgent 权限系统 (优先级: P1)

### 3.1 目标
完善权限系统，对齐 OpenCode：
- PermissionAction (allow/ask/deny)
- 通配符规则匹配
- 用户确认流程

### 3.2 设计来源
- `/docs/design/young-agent-core.md` Section 6
- `/docs/design/agent-design.md` Section 4.4

### 3.3 实现任务

| 任务 | 描述 | 优先级 |
|------|------|--------|
| PM-01 | 完善 PermissionAction 枚举 | P1 |
| PM-02 | 实现 PermissionRule 匹配 | P1 |
| PM-03 | 实现通配符匹配 (参考 OpenCode Wildcard) | P1 |
| PM-04 | 实现用户确认流程 | P1 |
| PM-05 | 集成到 Agent 执行流程 | P1 |

### 3.4 引用代码
- 权限系统: 参考 OpenCode `permission/next.ts`
- 规则解析: 参考 OpenCode `fromConfig()`

### 3.5 产出
```
src/agents/
├── permission.py      # 增强现有实现
├── evaluator.py       # 新增: PermissionEvaluator
└── rules.py          # 新增: 规则匹配
```

---

## 阶段 4: Task Dispatch 系统 (优先级: P1)

### 4.1 目标
实现任务调度系统：
- @mention 触发
- Session 层级管理
- 结果聚合

### 4.2 设计来源
- `/docs/design/young-agent-core.md` Section 5

### 4.3 实现任务

| 任务 | 描述 | 优先级 |
|------|------|--------|
| TD-01 | 实现 TaskDispatchParams | P1 |
| TD-02 | 实现 TaskDispatcher | P1 |
| TD-03 | 实现 Session 管理 | P1 |
| TD-04 | 实现 @mention 解析 | P2 |
| TD-05 | 实现结果聚合 | P1 |

### 4.4 引用代码
- Task Dispatch: 参考 OpenCode `tool/task.ts`

### 4.5 产出
```
src/agents/
├── dispatcher.py      # 增强现有实现
├── task.py           # 新增: 任务定义
└── session.py        # 新增: 会话管理
```

---

## 阶段 5: EvaluationHub 完善 (优先级: P2)

### 5.1 目标
完善评估中心：
- 索引构建
- 多维搜索
- 与 Package Manager 集成

### 5.2 设计来源
- `/docs/design/evaluation-hub-design.md`

### 5.3 实现任务

| 任务 | 描述 | 优先级 |
|------|------|--------|
| EH-01 | 实现 IndexBuilder | P2 |
| EH-02 | 实现多维搜索 | P2 |
| EH-03 | 实现 Package 加载 | P2 |
| EH-04 | 实现 EvalSubAgent | P2 |

### 5.4 产出
```
src/evaluation/
├── hub.py            # 增强现有实现
├── indexer.py        # 新增: 索引构建
└── search.py         # 新增: 多维搜索
```

---

## 阶段 6: CLI 完善 (优先级: P1)

### 6.1 目标
完善 CLI 命令集：
- llm 管理命令
- agent 配置命令
- 包管理命令

### 6.2 设计来源
- `/docs/design/cli-integration-design.md`

### 6.3 实现任务

| 任务 | 描述 | 优先级 |
|------|------|--------|
| CLI-01 | 实现 openyoung llm 命令集 | P0 |
| CLI-02 | 实现 openyoung agent 命令集 | P1 |
| CLI-03 | 实现 openyoung config 命令集 | P1 |
| CLI-04 | 实现 openyoung source 命令集 | P2 |

### 6.4 产出
```
src/cli/
├── main.py           # 增强现有实现
├── commands/
│   ├── __init__.py
│   ├── llm.py       # 新增: llm 命令
│   ├── agent.py     # 新增: agent 命令
│   ├── config.py   # 新增: config 命令
│   └── source.py   # 新增: source 命令
└── utils.py         # 增强现有实现
```

---

## 执行顺序

```
阶段 1 (PM) ──┬──> 阶段 2 (SL)
               │          │
               │          ▼
               │    阶段 3 (Permission)
               │          │
               │          ▼
               │    阶段 4 (Task Dispatch)
               │          │
               ▼          ▼
           阶段 6 (CLI) ◄───► 阶段 5 (Evaluation)

注意: 阶段 1 和 2 可以并行开始
```

---

## 关键依赖

| 任务 | 依赖 |
|------|------|
| SL-05 (集成 PM) | PM-01, PM-02, PM-03 |
| CLI-01 (llm 命令) | PM-03, PM-06 |
| TD-02 (Dispatcher) | PM-01 |
| EH-03 (Package 加载) | PM-01, PM-02, PM-03 |

---

## 验收标准

每个阶段完成后:
1. 单元测试通过
2. 与设计文档对齐
3. CLI 命令可用

---

## 更新日志

| 日期 | 内容 |
|------|------|
| 2026-03-02 | 创建执行计划 |

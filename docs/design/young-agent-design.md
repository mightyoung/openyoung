#SP|# OpenYoung - YoungAgent 设计文档
#KM|
#QK|> 项目: OpenYoung (全新项目)
#TS|> Agent: YoungAgent
#VB|> 基于 OpenCode、Claude Code、Codex 架构改造
#BJ|> 版本: 1.0.0
#SX|> 更新日期: 2026-03-01
#XW|
#SM|> 关联: [integrat-design.md](./integrat-design.md) - 整体项目集成架构
#MK|---

> 项目: OpenYoung (全新项目)
> Agent: YoungAgent
> 基于 OpenCode、Claude Code、Codex 架构改造
> 版本: 1.0.0
> 更新日期: 2026-03-01

---

## 文档结构

YoungAgent 设计文档已拆分为以下子文件：

| 子文件 | 内容 | 行数 |
|--------|------|------|
| [young-agent-core.md](young-agent-core.md) | 核心架构（类型、Agent、SubAgent、权限、配置） | ~610 |
| [young-agent-flow.md](young-agent-flow.md) | Flow Skill 集成 | ~285 |
| [young-agent-prompt.md](young-agent-prompt.md) | 提示词模板系统 | ~330 |
| [young-agent-memory.md](young-agent-memory.md) | 记忆系统（Checkpoint、Auto Memory、Skills） | ~400 |
| [young-agent-integration.md](young-agent-integration.md) | 外部系统集成（包含 EvalSubAgent） | ~360 |

---

## 快速导航

### 核心架构
- **架构概述** → [young-agent-core.md](./young-agent-core.md#1-架构概述)
- **核心类型定义** → [young-agent-core.md](./young-agent-core.md#2-核心类型定义)
- **Agent 类** → [young-agent-core.md](./young-agent-core.md#3-核心-agent-类)
- **SubAgent 系统** → [young-agent-core.md](./young-agent-core.md#4-subagent-系统)
- **Task Dispatch** → [young-agent-core.md](./young-agent-core.md#5-task-dispatch-系统)
- **权限系统** → [young-agent-core.md](./young-agent-core.md#6-权限系统)
- **配置格式** → [young-agent-core.md](./young-agent-core.md#7-配置格式)

### Flow Skill
- **Flow Skill 集成** → [young-agent-flow.md](./young-agent-flow.md)

### 提示词
- **提示词模板系统** → [young-agent-prompt.md](./young-agent-prompt.md)
- **默认提示词** → [young-agent-prompt.md](./young-agent-prompt.md#3-默认提示词模板-完整版---manus-方法论)

### 记忆系统
- **Checkpoint 系统** → [young-agent-memory.md](./young-agent-memory.md#1-checkpoint-系统-来自-claude-code)
- **Auto Memory** → [young-agent-memory.md](./young-agent-memory.md#2-auto-memory-系统-来自-claude-code)
- **Skills Progressive Disclosure** → [young-agent-memory.md](./young-agent-memory.md#3-skills-progressive-disclosure-来自-codex)

### 外部集成
- **Package Manager 集成** → [young-agent-integration.md](./young-agent-integration.md#2-与-package-manager-集成)
- **DataCenter 集成** → [young-agent-integration.md](./young-agent-integration.md#3-与-datacenter-集成)
- **EvaluationHub/EvalSubAgent** → [young-agent-integration.md](./young-agent-integration.md#4-与-evaluationhubevalsubagent-集成)
- **Evolver 集成** → [young-agent-integration.md](./young-agent-integration.md#5-与-evolver-集成)

---

## 设计原则

1. **零外部依赖** - 核心仅使用 Python 标准库
2. **配置驱动** - YAML/Markdown 定义 Agent
3. **权限优先** - 每次工具调用前检查权限
4. **可扩展** - Flow Skill 编排工作流
5. **可成长** - Evolver 自进化能力
6. **可回滚** - Checkpoint 支持文件编辑回滚
7. **记忆分层** - 显式 + 自动分层记忆
8. **渐进加载** - Skills 按需加载避免上下文膨胀

---

## 相关文档

- [EvaluationHub 设计](../evaluation-hub-design.md)
- [Package Manager 设计](../package-manager-design.md)
- [DataCenter 设计](../datacenter-design.md)
- [Evolver 设计](../evolver-design.md)

---

*本文档基于 OpenCode、Claude Code、Codex 架构改造*

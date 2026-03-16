# OpenYoung 系统架构图

## 架构概览

此文档展示OpenYoung AI Agent平台的系统架构。

![OpenYoung Architecture](./openyoung-architecture.excalidraw.md)

## 架构层次

| 层次 | 组件 | 描述 |
|------|------|------|
| **Core Layer** | LLM Providers, Agent Engine, Tool Executor | 核心代理引擎 |
| **Runtime Layer** | Sandbox, Evaluator, Tracing | 运行时环境 |
| **Hub Layer** | DataCenter, EvaluationHub, EvolutionEngine, Harness | 数据持久化与评估 |
| **Skills Layer** | External Sources, Heartbeat, Package Manager | 技能扩展 |
| **UI Layer** | CLI REPL, API Server | 用户界面 |

## 使用方式

1. 将 `.excalidraw.md` 文件移动到 Obsidian vault 的 `excalidraw` 文件夹
2. 在 Obsidian 中打开文件
3. 选择 "MORE OPTIONS" → "Switch to EXCALIDRAW VIEW" 查看图表

## 图表列表

| 文件 | 描述 |
|------|------|
| `openyoung-architecture.excalidraw.md` | OpenYoung系统架构流程图 |
| `agent-workflow.excalidraw.md` | Agent工作流程思维导图 |

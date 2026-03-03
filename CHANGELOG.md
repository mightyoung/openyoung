# Changelog / 更新日志

[English](#english) | [中文](#中文)

---

## English

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

### [1.0.0] - 2026-03-03

#### Added
- Initial release of OpenYoung AI Agent Platform
- Multi-LLM support (OpenAI, Anthropic, local models)
- Interactive REPL mode for CLI
- Tool execution system (bash, read, write, edit, glob, grep)
- Agent system with permission control and session management
- Package manager for dynamic skill loading
- Evaluation framework with multiple evaluators (code, task, llm_judge, safety)
- Evolution engine with gene-based self-improvement
- Data persistence for all components (DataCenter, EvaluationHub, EvolutionEngine, Harness)
- Trace collection and recording

#### Features
- `openyoung llm list` - List available LLM configurations
- `openyoung agent list` - List available agents
- `openyoung run <name>` - Run an agent in interactive mode
- Built-in tools: bash, write, edit, read, glob, grep

---

## 中文

本项目的所有重要变更都将记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
本项目遵循 [语义化版本控制](https://semver.org/lang/zh-CN/)。

### [1.0.0] - 2026-03-03

#### 新增
- OpenYoung AI Agent 平台初始发布
- 多 LLM 支持（OpenAI、Anthropic、本地模型）
- CLI 交互式 REPL 模式
- 工具执行系统（bash、read、write、edit、glob、grep）
- 带权限控制和会话管理的代理系统
- 用于动态技能加载的包管理器
- 包含多个评估器的评估框架（code、task、llm_judge、safety）
- 基于基因的自我改进进化引擎
- 所有组件的数据持久化（DataCenter、EvaluationHub、EvolutionEngine、Harness）
- 追踪收集和记录

#### 功能
- `openyoung llm list` - 列出可用的 LLM 配置
- `openyoung agent list` - 列出可用的代理
- `openyoung run <名称>` - 在交互模式下运行代理
- 内置工具：bash、write、edit、read、glob、grep

# OpenYoung

[English](#english) | [中文](#中文)

---

## English

### Overview

OpenYoung is an AI Agent Platform that provides a unified interface for interacting with various large language models (LLMs). It offers a CLI tool for executing tasks, managing packages, and running agents in an interactive REPL environment.

### Features

- **Multi-LLM Support**: Connect to various LLM providers (OpenAI, Anthropic, local models, etc.)
- **Interactive REPL**: Enter conversation mode directly from CLI, similar to Claude Code, OpenCode, or Codex
- **Tool Execution**: Execute bash commands, read/write files, search code, and more
- **Agent System**: Built-in agent system with permission control and session management
- **Package Manager**: Load and manage skill packages dynamically
- **Evaluation Framework**: Comprehensive evaluation system with multiple evaluators
- **Evolution Engine**: Gene-based evolution system for agent self-improvement
- **Data Persistence**: All component data persists to disk for future sessions

### Installation

```bash
# Install from source
pip install -e .

# Or install from PyPI (when published)
pip install openyoung
```

### Quick Start

```bash
# List available LLMs
openyoung llm list

# List available agents
openyoung agent list

# Run default agent (interactive mode)
openyoung run default

# Or run a specific agent
openyoung run <agent-name>
```

### CLI Commands

| Command | Description |
|---------|-------------|
| `openyoung llm list` | List available LLM configurations |
| `openyoung agent list` | List available agents |
| `openyoung run <name>` | Run an agent |
| `openyoung --help` | Show help message |

### Configuration

Create a `.env` file in your project root:

```bash
# OpenAI
OPENAI_API_KEY=your-api-key
OPENAI_BASE_URL=https://api.openai.com/v1

# Anthropic (optional)
ANTHROPIC_API_KEY=your-anthropic-key
```

### Architecture

```
openyoung/
├── src/
│   ├── agents/          # Agent system
│   ├── cli/             # CLI interface
│   ├── core/            # Core types
│   ├── datacenter/      # Trace collection
│   ├── evaluation/      # Evaluation framework
│   ├── evolver/         # Evolution engine
│   ├── harness/         # Runtime harness
│   ├── llm/             # LLM clients
│   ├── memory/          # Memory system
│   ├── package_manager/ # Package management
│   ├── prompts/         # Prompt templates
│   ├── skills/          # Skill system
│   └── tools/           # Tool executor
├── tests/               # Test suite
└── docs/               # Documentation
```

### Development

```bash
# Run tests
pytest tests/

# Run specific test file
pytest tests/agents/test_dispatcher.py
```

### License

MIT License - see LICENSE file for details

---

## 中文

### 概述

OpenYoung是一个 AI Agent 平台，提供统一的接口来与各种大型语言模型（LLM）交互。它提供 CLI 工具来执行任务、管理包，并在交互式 REPL 环境中运行代理。

### 功能特性

- **多 LLM 支持**：连接各种 LLM 提供商（OpenAI、Anthropic、本地模型等）
- **交互式 REPL**：直接从 CLI 进入对话模式，类似于 Claude Code、OpenCode 或 Codex
- **工具执行**：执行 bash 命令、读写文件、搜索代码等
- **代理系统**：内置代理系统，带有权限控制和会话管理
- **包管理器**：动态加载和管理技能包
- **评估框架**：综合评估系统，包含多个评估器
- **进化引擎**：基于基因的进化系统，用于代理自我改进
- **数据持久化**：所有组件数据持久化到磁盘，供后续会话使用

### 安装

```bash
# 从源码安装
pip install -e .

# 或从 PyPI 安装（发布后）
pip install openyoung
```

### 快速开始

```bash
# 列出可用的 LLM
openyoung llm list

# 列出可用的代理
openyoung agent list

# 运行默认代理（交互模式）
openyoung run default

# 或运行特定代理
openyoung run <代理名称>
```

### CLI 命令

| 命令 | 描述 |
|------|------|
| `openyoung llm list` | 列出可用的 LLM 配置 |
| `openyoung agent list` | 列出可用的代理 |
| `openyoung run <名称>` | 运行代理 |
| `openyoung --help` | 显示帮助信息 |

### 配置

在项目根目录创建 `.env` 文件：

```bash
# OpenAI
OPENAI_API_KEY=你的-api-key
OPENAI_BASE_URL=https://api.openai.com/v1

# Anthropic（可选）
ANTHROPIC_API_KEY=你的-anthropic-key
```

### 架构

```
openyoung/
├── src/
│   ├── agents/          # 代理系统
│   ├── cli/             # CLI 接口
│   ├── core/            # 核心类型
│   ├── datacenter/      # 追踪收集
│   ├── evaluation/      # 评估框架
│   ├── evolver/         # 进化引擎
│   ├── harness/         # 运行时管理器
│   ├── llm/             # LLM 客户端
│   ├── memory/          # 记忆系统
│   ├── package_manager/ # 包管理
│   ├── prompts/         # 提示模板
│   ├── skills/          # 技能系统
│   └── tools/           # 工具执行器
├── tests/               # 测试套件
└── docs/               # 文档
```

### 开发

```bash
# 运行测试
pytest tests/

# 运行特定测试文件
pytest tests/agents/test_dispatcher.py
```

### 许可证

MIT 许可证 - 详见 LICENSE 文件

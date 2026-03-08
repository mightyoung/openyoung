# OpenYoung

**智能 Agent 发现与部署平台** | Intelligent Agent Discovery & Deployment Platform

[English](#english) | [中文](#中文)

---

## English

### What is OpenYoung?

OpenYoung is an AI agent platform that **automatically discovers, evaluates, and deploys** high-quality agents based on your task input.

Instead of manually searching and configuring agents, just describe what you want to do — OpenYoung handles the rest.

### Core Features

```
┌─────────────────────────────────────────────────────────────────┐
│                      OpenYoung Pipeline                          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  Intent        │
                    │  Analysis      │ ◄── LLM-powered intent detection
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │  Semantic       │ ◄── Vector similarity search
                    │  Search        │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │  Quality        │ ◄── Multi-dimensional evaluation
                    │  Evaluation     │
                    └────────┬────────┘
                             │
                    ┌────────┴────────┐
                    ▼                 ▼
              ┌─────────┐       ┌─────────┐
              │ Badges  │       │ Version │
              │ Display │       │ History │
              └────┬────┘       └────┬────┘
                   │                 │
                   └────────┬────────┘
                            ▼
                    ┌─────────────────┐
                    │  Auto-Config   │ ◄── Always Skills loading
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │  Execute Task  │
                    └─────────────────┘
```

| Feature | Description |
|---------|-------------|
| **Semantic Search** | Find agents using natural language, not keywords |
| **Quality Evaluation** | 6-dimension scoring: completeness, validity, dependencies, documentation, security, runtime |
| **Intent Analysis** | Understand what you want to do, recommend the right agent |
| **Badge System** | Visual quality indicators: Verified, Top Rated, Trending, New, Popular |
| **Version Management** | Track agent versions with SemVer support |
| **Usage Tracking** | Monitor which agents are most popular |

### Quick Start

```bash
# Run agent with natural language
openyoung run "帮我写一个排序算法"

# List all available agents with badges
openyoung agent list --all --badges --stats

# Search agents semantically
openyoung agent search "代码审查"

# Compare two agents
openyoung agent compare default coder

# Analyze your intent
openyoung agent intent "我想要自动化测试"

# Check version history
openyoung agent versions agent-coder
openyoung agent version-add agent-coder 1.0.0 --changelog "Initial release"
```

### CLI Commands

| Command | Description |
|---------|-------------|
| `openyoung run <task>` | Run agent with task description |
| `openyoung agent list` | List available agents |
| `openyoung agent search <query>` | Semantic search agents |
| `openyoung agent compare <a> <b>` | Compare two agents |
| `openyoung agent evaluate <agent>` | Quality evaluation |
| `openyoung agent intent <query>` | Intent analysis |
| `openyoung agent stats` | Usage statistics |
| `openyoung agent versions <agent>` | Version history |
| `openyoung import github <repo>` | Import from GitHub |
| `openyoung --help` | Show help |

### Agent Package Structure

```
packages/
├── agent-coder/
│   ├── agent.yaml          # Agent configuration
│   ├── pyproject.toml     # Dependencies
│   └── src/               # Agent code
└── agent-reviewer/
    ├── agent.yaml
    └── pyproject.toml
```

### Configuration

Create `.env` in your project root:

```bash
# Required: At least one LLM provider
OPENAI_API_KEY=your-openai-key
# or
ANTHROPIC_API_KEY=your-anthropic-key

# Optional: Vector search (for semantic search)
DASHSCOPE_API_KEY=your-dashscope-key
```

### Architecture

```
openyoung/
├── src/
│   ├── agents/           # Agent system
│   ├── cli/              # CLI interface
│   ├── core/             # Core types
│   ├── evaluation/       # Quality evaluation
│   ├── llm/              # LLM clients
│   ├── memory/           # Vector store
│   ├── package_manager/  # Discovery, badges, versions
│   └── runtime/          # AI Docker runtime
├── packages/             # Agent packages
├── skills/              # Always-loaded skills
└── docs/                # Documentation
```

---

## AI Docker

OpenYoung includes a built-in **AI Docker sandbox execution environment** that provides secure and controlled code execution for AI Agents.

### Core Features

| Feature | Description |
|---------|-------------|
| **Sandbox Isolation** | Resource limits (CPU/Memory/Time), network access control |
| **Security Policy** | Command whitelist, dangerous pattern detection, file path validation |
| **Instance Pool** | Auto-scaling, instance pre-warming, state persistence |
| **Audit Logging** | Execution records, statistics, JSONL format |

### Usage

```python
from src.agents import YoungAgent

agent = YoungAgent(config)
agent.enable_sandbox(max_memory_mb=512)
# or
agent.enable_sandbox_pool(min_size=2, max_size=10)
```

### License

MIT License

---

## 中文

### 什么是 OpenYoung？

OpenYoung 是一个 **智能 Agent 发现与部署平台**，能够根据你的任务输入自动发现、评估和部署高质量 Agent。

无需手动搜索和配置 Agent，只需描述你想要做什么 —— OpenYoung 会帮你完成其余工作。

### 核心功能

```
┌─────────────────────────────────────────────────────────────────┐
│                      OpenYoung 工作流程                         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  意图理解       │ ◄── LLM 驱动的意图分析
                    │  Intent        │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │  语义搜索       │ ◄── 向量相似度匹配
                    │  Semantic      │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │  质量评估       │ ◄── 多维度评分
                    │  Quality       │
                    └────────┬────────┘
                             │
                    ┌────────┴────────┐
                    ▼                 ▼
              ┌─────────┐       ┌─────────┐
              │  徽章系统 │       │ 版本管理 │
              │  Badges │       │ Versions│
              └────┬────┘       └────┬────┘
                   │                 │
                   └────────┬────────┘
                            ▼
                    ┌─────────────────┐
                    │  自动配置       │ ◄── Always Skills 加载
                    │  Auto-Config   │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │  执行任务       │
                    │  Execute       │
                    └─────────────────┘
```

| 功能 | 描述 |
|------|------|
| **语义搜索** | 用自然语言而非关键词搜索 Agent |
| **质量评估** | 6 维度评分：完整性、有效性、依赖、文档、安全、运行时 |
| **意图理解** | 理解你想要做什么，推荐合适的 Agent |
| **徽章系统** | 可视化质量标识：官方验证、高评分、趋势上升、新增、热门 |
| **版本管理** | SemVer 版本的版本历史追踪 |
| **使用追踪** | 监控哪些 Agent 最受欢迎 |

### 快速开始

```bash
# 用自然语言运行 agent
openyoung run "帮我写一个排序算法"

# 列出所有 agents（含徽章和统计）
openyoung agent list --all --badges --stats

# 语义搜索 agents
openyoung agent search "代码审查"

# 对比两个 agents
openyoung agent compare default coder

# 分析你的意图
openyoung agent intent "我想要自动化测试"

# 查看版本历史
openyoung agent versions agent-coder
openyoung agent version-add agent-coder 1.0.0 --changelog "初始版本"
```

### CLI 命令

| 命令 | 描述 |
|------|------|
| `openyoung run <任务>` | 使用任务描述运行 agent |
| `openyoung agent list` | 列出可用 agents |
| `openyoung agent search <查询>` | 语义搜索 agents |
| `openyoung agent compare <a> <b>` | 对比两个 agents |
| `openyoung agent evaluate <agent>` | 质量评估 |
| `openyoung agent intent <查询>` | 意图分析 |
| `openyoung agent stats` | 使用统计 |
| `openyoung agent versions <agent>` | 版本历史 |
| `openyoung import github <仓库>` | 从 GitHub 导入 |
| `openyoung --help` | 显示帮助 |

### Agent 包结构

```
packages/
├── agent-coder/
│   ├── agent.yaml        # Agent 配置
│   ├── pyproject.toml   # 依赖
│   └── src/             # Agent 代码
└── agent-reviewer/
    ├── agent.yaml
    └── pyproject.toml
```

### 配置

在项目根目录创建 `.env` 文件：

```bash
# 必需：至少一个 LLM 提供商
OPENAI_API_KEY=your-openai-key
# 或
ANTHROPIC_API_KEY=your-anthropic-key

# 可选：向量搜索（用于语义搜索）
DASHSCOPE_API_KEY=your-dashscope-key
```

### 项目架构

```
openyoung/
├── src/
│   ├── agents/           # Agent 系统
│   ├── cli/              # CLI 接口
│   ├── core/             # 核心类型
│   ├── evaluation/       # 质量评估
│   ├── llm/              # LLM 客户端
│   ├── memory/           # 向量存储
│   ├── package_manager/  # 发现、徽章、版本
│   └── runtime/          # AI Docker 运行时
├── packages/             # Agent 包
├── skills/              # Always Skills
└── docs/                 # 文档
```

---

## AI Docker

OpenYoung 内置 **AI Docker 沙箱执行环境**，为 AI Agent 提供安全可控的代码执行能力。

### 核心功能

| 功能 | 描述 |
|------|------|
| **沙箱隔离** | 资源限制 (CPU/Memory/Time)，网络访问控制 |
| **安全策略** | 命令白名单，危险模式检测，文件路径验证 |
| **实例池** | 自动扩缩容，预热实例，状态持久化 |
| **审计日志** | 执行记录，统计查询 |

### 使用方式

```python
from src.agents import YoungAgent

agent = YoungAgent(config)
agent.enable_sandbox(max_memory_mb=512)
# 或
agent.enable_sandbox_pool(min_size=2, max_size=10)
```

### 许可证

MIT License

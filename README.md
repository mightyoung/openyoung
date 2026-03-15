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
| `openyoung agent info <agent>` | Show agent details |
| `openyoung agent search <query>` | Semantic search agents |
| `openyoung agent compare <a> <b>` | Compare two agents |
| `openyoung agent evaluate <agent>` | Quality evaluation |
| `openyoung agent intent <query>` | Intent analysis |
| `openyoung eval list` | List evaluation metrics |
| `openyoung eval trend <agent>` | Show evaluation trend |
| `openyoung eval run <task>` | Run evaluation on a task |
| `openyoung eval server` | Start eval API server |
| `openyoung data runs` | List run records |
| `openyoung data list` | List run records (alias) |
| `openyoung memory list` | List memories |
| `openyoung memory search <query>` | Search memories |
| `openyoung mcp servers` | List MCP servers |
| `openyoung skills list` | List skills |
| `openyoung config list` | List configuration |
| `openyoung llm list` | List LLM providers |
| `openyoung package list` | List packages |
| `openyoung source list` | List sources |
| `openyoung channel list` | List channels |
| `openyoung templates list` | List templates |
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

## Reinforcement Learning (RL)

OpenYoung supports optional **GPU-accelerated Reinforcement Learning** for agent self-evolution and optimization.

### Core Features

| Feature | Description |
|---------|-------------|
| **Multi-Backend Support** | CUDA (NVIDIA), MPS (Apple Silicon), CPU, Vulkan (ARM RK3588) |
| **GRPO** | Group Relative Policy Optimization - lightweight training for M1/medium GPUs |
| **GiGPO** | Group-in-Group Policy Optimization - two-layer advantage for complex agents |
| **Experience Collection** | Collect task experiences without GPU (default mode) |
| **Docker Support** | Ready-to-deploy RL training with Docker Compose |

### Supported Hardware

| Hardware | Recommended Mode | Notes |
|----------|-----------------|-------|
| NVIDIA GPU (CUDA) | GiGPO | Full two-layer advantage |
| Apple Silicon (MPS) | GRPO | Memory-efficient training |
| CPU only | Collection Only | Experience collection only |
| ARM (RK3588) | Collection Only | Future: Vulkan support |

### Usage

```python
from src.agents.rl import create_rl_engine, RLConfig, RLMode

# Auto-detect hardware and create engine
engine = create_rl_engine()

# Or specify mode manually
config = RLConfig(mode=RLMode.GRPO)  # collection_only / grpo / gigpo
engine = create_rl_engine(config)
```

### Docker Deployment

```bash
# Start RL training service
docker-compose -f docker-compose.rl.yml up -d

# With NVIDIA GPU
docker-compose -f docker-compose.rl.yml up -d --profile gpu
```

### Configuration

```yaml
# config/rl.yaml
rl:
  enabled: true
  mode: collection_only  # collection_only | grpo | gigpo
  device: auto  # auto | cuda | mps | cpu
  grpo:
    learning_rate: 1.0e-5
    clip_epsilon: 0.2
    group_size: 4
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

### Enhanced Security (2025 Best Practices)

| Security Feature | Description |
|-----------------|-------------|
| **Working Directory Restriction** | Files can only be accessed within configured working directory |
| **Path Traversal Prevention** | Blocks `..`, `/proc`, `/sys`, `/dev` attacks |
| **Network Isolation** | Domain whitelist/blacklist, default deny |
| **MCP Server Security** | Command validation, environment sanitization |
| **Audit Logging** | All security events logged |

### Usage

```python
from src.runtime.sandbox import SandboxPolicy, SecurityPolicyEngine

# Configure security policy
policy = SandboxPolicy(
    working_directory="/tmp/sandbox",       # Restrict to working dir
    restrict_to_working_dir=True,
    allow_network=True,
    allowed_domains=["api.openai.com"],
)
engine = SecurityPolicyEngine(policy)

# Check file access
safe, reason = engine.check_path_traversal("/tmp/sandbox/file.txt")  # ALLOWED
safe, reason = engine.check_path_traversal("/etc/passwd")  # BLOCKED
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
| `openyoung agent info <agent>` | 显示 agent 详情 |
| `openyoung agent search <查询>` | 语义搜索 agents |
| `openyoung agent compare <a> <b>` | 对比两个 agents |
| `openyoung agent evaluate <agent>` | 质量评估 |
| `openyoung agent intent <查询>` | 意图分析 |
| `openyoung eval list` | 列出评估指标 |
| `openyoung eval trend <agent>` | 显示评估趋势 |
| `openyoung eval run <任务>` | 运行任务评估 |
| `openyoung eval server` | 启动评估 API 服务器 |
| `openyoung data runs` | 列出运行记录 |
| `openyoung data list` | 列出运行记录（别名） |
| `openyoung memory list` | 列出记忆 |
| `openyoung memory search <查询>` | 搜索记忆 |
| `openyoung mcp servers` | 列出 MCP 服务器 |
| `openyoung skills list` | 列出技能 |
| `openyoung config list` | 列出配置 |
| `openyoung llm list` | 列出 LLM 提供商 |
| `openyoung package list` | 列出包 |
| `openyoung source list` | 列出数据源 |
| `openyoung channel list` | 列出通道 |
| `openyoung templates list` | 列出模板 |
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

## 强化学习 (RL)

OpenYoung 支持可选的 **GPU 加速强化学习**，用于 Agent 自我进化与优化。

### 核心功能

| 功能 | 描述 |
|------|------|
| **多后端支持** | CUDA (NVIDIA)、MPS (Apple Silicon)、CPU、Vulkan (ARM RK3588) |
| **GRPO** | 组相对策略优化 - 适用于 M1/中等 GPU 的轻量训练 |
| **GiGPO** | 组内组策略优化 - 复杂 Agent 的双层优势估计 |
| **经验收集** | 无需 GPU 的经验收集（默认模式） |
| **Docker 支持** | 开箱即用的 RL 训练服务部署 |

### 支持的硬件

| 硬件 | 推荐模式 | 备注 |
|------|---------|------|
| NVIDIA GPU (CUDA) | GiGPO | 完整双层优势 |
| Apple Silicon (MPS) | GRPO | 内存高效训练 |
| 仅 CPU | 仅收集 | 经验收集模式 |
| ARM (RK3588) | 仅收集 | 未来支持: Vulkan |

### 使用方式

```python
from src.agents.rl import create_rl_engine, RLConfig, RLMode

# 自动检测硬件并创建引擎
engine = create_rl_engine()

# 或手动指定模式
config = RLConfig(mode=RLMode.GRPO)  # collection_only / grpo / gigpo
engine = create_rl_engine(config)
```

### Docker 部署

```bash
# 启动 RL 训练服务
docker-compose -f docker-compose.rl.yml up -d

# 使用 NVIDIA GPU
docker-compose -f docker-compose.rl.yml up -d --profile gpu
```

### 配置

```yaml
# config/rl.yaml
rl:
  enabled: true
  mode: collection_only  # collection_only | grpo | gigpo
  device: auto  # auto | cuda | mps | cpu
  grpo:
    learning_rate: 1.0e-5
    clip_epsilon: 0.2
    group_size: 4
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

### 安全增强 (2025最佳实践)

| 安全功能 | 描述 |
|---------|------|
| **工作目录限制** | 文件只能访问配置的工作目录 |
| **路径穿越防护** | 阻止 `..`、`/proc`、`/sys`、`/dev` 攻击 |
| **网络隔离** | 域名白名单/黑名单，默认拒绝 |
| **MCP服务器安全** | 命令验证，环境变量清理 |
| **审计日志** | 所有安全事件记录 |

### 使用方式

```python
from src.runtime.sandbox import SandboxPolicy, SecurityPolicyEngine

# 配置安全策略
policy = SandboxPolicy(
    working_directory="/tmp/sandbox",       # 限制工作目录
    restrict_to_working_dir=True,
    allow_network=True,
    allowed_domains=["api.openai.com"],
)
engine = SecurityPolicyEngine(policy)

# 检查文件访问
safe, reason = engine.check_path_traversal("/tmp/sandbox/file.txt")  # 允许
safe, reason = engine.check_path_traversal("/etc/passwd")  # 阻止
```

### 许可证

MIT License

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
| `openyoung peas report <data>` | Generate PEAS verification report |
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
│   ├── agents/                # Agent system
│   │   ├── harness/           # ✅ Harness-centric AI factory (NEW)
│   │   │   ├── engine.py     # Core execution engine
│   │   │   ├── graph.py      # Task graph
│   │   │   ├── task_compiler.py    # Task → Graph compiler
│   │   │   ├── resource_manager.py  # Resource allocation
│   │   │   ├── harness_runner.py    # Lifecycle management
│   │   │   └── types.py      # Streaming types
│   │   ├── execution/         # ✅ Execution layer (NEW)
│   │   ├── commands/         # ✅ CLI commands (NEW - modular)
│   │   └── young_agent.py    # ✅ Refactored to ~400 lines
│   ├── cli/                  # ✅ Refactored to ~100 lines
│   │   ├── main.py           # Entry point (96 lines)
│   │   └── commands/         # Modular commands
│   ├── core/                 # Core types & infrastructure
│   │   ├── memory/          # ✅ Hierarchical memory system
│   │   ├── events.py         # EventBus
│   │   ├── heartbeat.py      # Heartbeat scheduler
│   │   └── langgraph_*.py    # LangGraph integration
│   ├── hub/                   # Hub system
│   │   └── evaluate/         # ✅ Unified evaluation (NEW)
│   │       ├── harness.py    # Evaluation harness
│   │       ├── runner.py     # Eval runner
│   │       └── benchmark.py  # Benchmark tools
│   ├── peas/                  # ✅ Plan-Execution Alignment System (PEAS)
│   │   ├── README.md         # PEAS documentation
│   │   ├── understanding/    # Markdown/HTML parsers
│   │   ├── verification/     # Drift detection, feature tracking
│   │   └── contract/         # Executable contracts
│   └── webui/                # Streamlit WebUI
├── packages/                 # Agent packages
├── skills/                   # Skills
├── tests/                    # Test suite (1084+ tests)
└── docs/                    # Documentation
```

### Refactoring Achievements

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| young_agent.py | 1665 lines | ~400 lines | -76% |
| cli/main.py | 2167 lines | ~96 lines | -96% |
| Harness coverage | 30% | 95% | +217% |
| Test coverage | ~20% | 80%+ | +300% |
| Code duplication | High | Minimal | ✅ |

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

## AI Sandbox

OpenYoung includes a **subprocess-based AI Sandbox** that provides secure and controlled code execution for AI Agents using `asyncio.subprocess` (not Docker containers).

**Architecture Note**: The sandbox uses a multi-backend design:
- **E2B** (recommended): Full microVM-based isolation with native network control
- **Docker**: Not yet implemented
- **Process** (fallback): Subprocess-based execution with basic security controls

### Core Features

| Feature | Description |
|---------|-------------|
| **Process Execution** | Uses `subprocess.run()` with timeout control |
| **Security Policy Engine** | Risk assessment, dangerous pattern detection |
| **Network Pattern Detection** | Blocks network commands (curl, wget, nc, etc.) when disabled |
| **Audit Logging** | Execution records, statistics |

### Security Features

The subprocess-based sandbox provides the following security controls:

| Security Feature | Description |
|-----------------|-------------|
| **Timeout Protection** | Execution time limit via subprocess timeout |
| **Network Command Blocking** | Prevents execution of network commands (curl, wget, nc, etc.) when `allow_network=False` |
| **Risk Assessment** | Code is scanned for dangerous patterns before execution |
| **Prompt Injection Detection** | Detects and blocks malicious prompt patterns |
| **Secret Scanning** | Detects exposed API keys, passwords, tokens |

**Known Limitations** (Process Backend):
- No CPU/Memory limits via `resource` module (subprocess-based)
- No filesystem isolation (process runs on host)
- No path traversal enforcement (requires containerization)
- No true network isolation (requires E2B or container)

For stronger security guarantees, use E2B backend which provides microVM-level isolation.

### Usage

```python
from src.runtime.sandbox import AISandbox, SandboxConfig, SandboxPolicy

# Create sandbox with security policy
config = SandboxConfig(
    working_directory="/tmp/sandbox",
    restrict_to_working_dir=True,
    allow_network=False,
    enable_prompt_detection=True,
    enable_secret_detection=True,
)
sandbox = AISandbox(config)

# Create a sandbox instance
sandbox_id = await sandbox.create(agent_id="my-agent")

# Execute code securely
result = await sandbox.execute(sandbox_id, "print('Hello, World!')", language="python")
```

### WebUI

OpenYoung provides a **Streamlit-based WebUI** for visual interaction with agents, sessions, and evaluations.

#### Core Features

| Feature | Description |
|---------|-------------|
| **Chat Interface** | Real-time streaming chat with AI agents |
| **Session Management** | Create, suspend, resume, delete persistent sessions |
| **Agent Management** | Browse and manage available agents |
| **Evaluation Dashboard** | View evaluation results and metrics |
| **SSE Streaming** | Server-Sent Events for real-time responses |

#### Quick Start

```bash
# Install dependencies
pip install -r webui/requirements.txt

# Start WebUI
streamlit run webui/app.py

# Or use the CLI
openyoung webui
```

#### Configuration

Edit `webui/utils/config.py`:

```python
API_BASE_URL = "http://localhost:8000"  # API server URL
API_KEY = ""  # Optional API key
TYPING_SPEED = 0.02  # Seconds between characters
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
| `openyoung peas report <data>` | 生成 PEAS 验证报告 |
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
│   ├── agents/                # Agent 系统
│   │   ├── harness/           # ✅ Harness驱动的AI工厂 (新增)
│   │   │   ├── engine.py     # 核心执行引擎
│   │   │   ├── graph.py      # 任务图
│   │   │   ├── task_compiler.py    # Task → Graph 编译器
│   │   │   ├── resource_manager.py  # 资源分配
│   │   │   ├── harness_runner.py    # 生命周期管理
│   │   │   └── types.py      # 流式类型
│   │   ├── execution/         # ✅ 执行层 (新增)
│   │   ├── commands/          # ✅ CLI 命令模块化 (新增)
│   │   └── young_agent.py     # ✅ 重构后约400行
│   ├── cli/                   # ✅ 重构后约100行
│   │   ├── main.py           # 入口 (96行)
│   │   └── commands/         # 模块化命令
│   ├── core/                  # 核心类型和基础设施
│   │   ├── memory/           # ✅ 分层记忆系统
│   │   ├── events.py         # 事件总线
│   │   ├── heartbeat.py      # 心跳调度器
│   │   └── langgraph_*.py    # LangGraph 集成
│   ├── hub/                   # Hub 系统
│   │   └── evaluate/          # ✅ 统一评估 (新增)
│   │       ├── harness.py     # 评估线束
│   │       ├── runner.py      # 评估运行器
│   │       └── benchmark.py   # 基准测试工具
│   ├── peas/                  # ✅ 规划执行对齐系统 (PEAS)
│   │   ├── README.md          # PEAS 文档
│   │   ├── understanding/     # Markdown/HTML 解析器
│   │   ├── verification/      # 偏离检测、功能追踪
│   │   └── contract/          # 可执行合约
│   └── webui/                # Streamlit WebUI
├── packages/                  # Agent 包
├── skills/                    # 技能
├── tests/                     # 测试套件 (119个测试)
└── docs/                     # 文档
```

### 重构成果

| 指标 | 重构前 | 重构后 | 改善 |
|------|--------|--------|------|
| young_agent.py | 1665行 | ~400行 | -76% |
| cli/main.py | 2167行 | ~96行 | -96% |
| Harness覆盖率 | 30% | 95% | +217% |
| 测试覆盖率 | ~20% | 80%+ | +300% |
| 代码重复 | 高 | 最低 | ✅ |
| 测试数量 | 119 | 1084+ | +810% |
| 测试数量 | 119 | 1084+ | +810% |

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

## AI 沙箱

OpenYoung 内置 **基于 Subprocess 的 AI 沙箱**，使用 `asyncio.subprocess`（非 Docker 容器）为 AI Agent 提供安全可控的代码执行能力。

**架构说明**: 沙箱采用多后端设计：
- **E2B** (推荐): 完整的 microVM 级别隔离，原生网络控制
- **Docker**: 尚未实现
- **Process** (后备): 基于 subprocess 的执行，提供基本安全控制

### 核心功能

| 功能 | 描述 |
|------|------|
| **进程执行** | 使用 `subprocess.run()` 配合 timeout 控制 |
| **安全策略引擎** | 风险评估，危险模式检测 |
| **网络模式检测** | 当禁用时阻止网络命令 (curl, wget, nc 等) |
| **审计日志** | 执行记录，统计查询 |

### 安全功能

基于 subprocess 的沙箱提供以下安全控制：

| 安全功能 | 描述 |
|---------|------|
| **超时保护** | 通过 subprocess timeout 限制执行时间 |
| **网络命令拦截** | 当 `allow_network=False` 时阻止网络命令 (curl, wget, nc 等) |
| **风险评估** | 执行前扫描代码中的危险模式 |
| **提示注入检测** | 检测并阻止恶意提示模式 |
| **敏感信息扫描** | 检测暴露的 API 密钥、密码、令牌 |

**已知限制** (Process 后端):
- 无 CPU/内存限制 via `resource` 模块 (基于 subprocess)
- 无文件系统隔离 (进程在主机上运行)
- 无路径穿越防护 (需要容器化)
- 无真正的网络隔离 (需要 E2B 或容器)

如需更强的安全保证，请使用 E2B 后端，其提供 microVM 级别的隔离。

### 使用方式

```python
from src.runtime.sandbox import AISandbox, SandboxConfig, SandboxPolicy

# 创建带安全策略的沙箱
config = SandboxConfig(
    working_directory="/tmp/sandbox",
    restrict_to_working_dir=True,
    allow_network=False,
    enable_prompt_detection=True,
    enable_secret_detection=True,
)
sandbox = AISandbox(config)

# 创建沙箱实例
sandbox_id = await sandbox.create(agent_id="my-agent")

# 安全执行代码
result = await sandbox.execute(sandbox_id, "print('Hello, World!')", language="python")
```

### WebUI

OpenYoung 提供基于 **Streamlit 的 WebUI**，用于可视化交互 Agent、会话和评估。

#### 核心功能

| 功能 | 描述 |
|------|------|
| **聊天界面** | 实时流式与 AI Agent 对话 |
| **会话管理** | 创建、暂停、恢复、删除持久会话 |
| **Agent 管理** | 浏览和管理可用的 Agent |
| **评估仪表盘** | 查看评估结果和指标 |
| **SSE 流式传输** | 服务器发送事件实现实时响应 |

#### 快速开始

```bash
# 安装依赖
pip install -r webui/requirements.txt

# 启动 WebUI
streamlit run webui/app.py

# 或使用 CLI
openyoung webui
```

#### 配置

编辑 `webui/utils/config.py`:

```python
API_BASE_URL = "http://localhost:8000"  # API 服务器地址
API_KEY = ""  # 可选的 API 密钥
TYPING_SPEED = 0.02  # 字符间隔秒数
```

### 许可证

MIT License

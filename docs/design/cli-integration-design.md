# OpenYoung CLI 与 Package Manager 集成设计

## 1. CLI 命令架构

### 1.1 命令结构

```bash
openyoung <command> [subcommand] [options] [args]

# 核心命令
openyoung run <agent> [task]      # 运行 Agent
openyoung install <package>       # 安装 Package
openyoung package <subcommand>    # Package 管理
openyoung agent <subcommand>      # Agent 管理
openyoung config <subcommand>     # 配置管理
```

### 1.2 Agent 运行命令

```bash
# 运行指定 Agent
openyoung run <agent-name> [task]
openyoung run default             # 运行默认 Agent
openyoung run @agent-config       # 运行配置文件中的 Agent

# 示例
openyoung run default "帮我写一个排序算法"
openyoung run code-agent "实现用户登录功能"
openyoung run ./agents/my-agent.yaml "修复登录 bug"
```

### 1.3 Package 安装命令

```bash
# 安装 Package
openyoung install <package>              # 从远程安装
openyoung install ./local-package         # 从本地安装
openyoung install gh:owner/repo           # 从 GitHub 安装

# Package 管理
openyoung package list                    # 列出已安装
openyoung package uninstall <package>      # 卸载
openyoung package update <package>        # 更新
```

## 2. Agent 配置格式

### 2.1 Agent 配置文件 (agent.yaml)

```yaml
# agents/code-agent.yaml
name: "code-agent"
version: "1.0.0"

# Agent 元信息
description: "代码开发专用 Agent"
author: "team@openyoung.io"
tags: [code, development, programming]

# 模型配置
model:
  provider: "deepseek"
  model: "deepseek-coder"
  temperature: 0.7
  max_tokens: 4096

# 工具配置
tools:
  - read
  - write
  - edit
  - bash
  - glob
  - grep

# 权限配置
permission:
  _global: ask
  rules:
    - tool_pattern: "bash"
      action: confirm
    - tool_pattern: "write"
      params_pattern:
        path: "*.py"
      action: allow

# Flow 配置
flow:
  default: "development"  # 使用 DevelopmentFlow
  available:
    - development
    - sequential
    - parallel

# Skill 配置
skills:
  - name: "coding-standards"
    package: "@openyoung/coding-skills"
  - name: "tdd-workflow"
    package: "@openyoung/tdd-plugin"

# 评估配置
evaluation:
  enabled: true
  metrics:
    - code_quality
    - task_completion
    - safety_score

# 依赖 Packages
dependencies:
  - "@openyoung/coding-skills"
  - "@openyoung/tdd-plugin"
```

### 2.2 默认 Agent 模板

```yaml
# agents/default.yaml
name: "default"
version: "1.0.0"
description: "OpenYoung 默认 Agent"

model:
  provider: "deepseek"
  model: "deepseek-chat"
  temperature: 0.7

tools:
  - read
  - write
  - edit
  - bash
  - glob
  - grep

flow:
  default: "development"
```

## 3. Agent Loader 设计

### 3.1 核心类图

```
AgentLoader
├── load_agent(name: str) -> AgentConfig
├── load_from_file(path: str) -> AgentConfig
├── load_default() -> AgentConfig
├── list_agents() -> List[AgentInfo]
└── validate_config(config: dict) -> bool

AgentRunner
├── prepare_environment(config: AgentConfig)
├── load_dependencies(config: AgentConfig)
├── create_agent(config: AgentConfig) -> YoungAgent
├── run(task: str) -> str
└── cleanup()
```

### 3.2 Agent 查找优先级

```
1. 指定路径: ./agents/my-agent.yaml
2. 当前目录: ./agent.yaml
3. 命名空间: @org/agent-name
4. 内置 Agents: default, code-agent, review-agent
5. 已安装 Packages: 从 package registry 查找
```

## 4. Package 与 Agent 集成

### 4.1 Package 作为 Agent 扩展

```
Agent
├── 基础配置 (model, tools, permission)
├── Skills (从 Package 加载)
│   ├── @openyoung/coding-skills
│   └── @custom/domain-skills
├── Flows (从 Package 加载)
│   └── @custom/flow-skill
└── Evaluators (从 Package 加载)
    └── @custom/eval-rules
```

### 4.2 Package 加载流程

```
openyoung run code-agent
    │
    ├─> AgentLoader.load_agent("code-agent")
    │       │
    │       ├─> 读取 agents/code-agent.yaml
    │       │
    │       └─> 解析 dependencies
    │
    └─> PackageManager.load_packages()
            │
            ├─> 安装 @openyoung/coding-skills
            ├─> 加载 SKILL.md
            │
            └─> 安装 @openyoung/tdd-plugin
                └─> 加载 evaluation rules
```

## 5. CLI 实现

### 5.1 命令行入口

```python
# cli/main.py
import click
from pathlib import Path

@click.group()
def cli():
    """OpenYoung - AI Agent Platform"""
    pass

@cli.command()
@click.argument('agent_name', default='default')
@click.argument('task', required=False)
@click.option('--config', '-c', help='Agent config file path')
@click.option('--model', '-m', help='Override model')
def run(agent_name, task, config, model):
    """Run an agent"""
    runner = AgentRunner()

    # 加载 Agent 配置
    agent_config = runner.load_agent(agent_name, config)

    # 覆盖模型
    if model:
        agent_config.model = model

    # 运行
    result = runner.run(task or "")
    print(result)

@cli.command()
@click.argument('package_name')
@click.option('--version', '-v', help='Specific version')
def install(package_name, version):
    """Install a package"""
    manager = PackageManager()
    asyncio.run(manager.install(package_name, version))
    print(f"Installed: {package_name}")

@cli.group()
def package():
    """Package management commands"""
    pass

@package.command('list')
def package_list():
    """List installed packages"""
    manager = PackageManager()
    for pkg in manager.list_packages():
        print(f"  {pkg}")

# 更多命令...
```

### 5.2 完整命令列表 (当前实现)

#### 核心命令

```bash
# 运行 Agent
openyoung run <agent> [task]           # 运行指定 Agent
openyoung run default "任务描述"         # 使用默认 Agent

# Agent 管理
openyoung agent list                     # 列出可用 Agent (P0 ✅)
openyoung agent info <agent>            # 查看 Agent 信息 (P0 ✅)
openyoung agent search <query>          # 语义搜索 Agent (P0 ✅)
openyoung agent compare <a> <b>         # 对比两个 Agent (P0 ✅)
openyoung agent evaluate <agent>         # 评估 Agent 质量
openyoung agent intent <query>          # 意图分析

# Package 管理
openyoung install <package>             # 安装 Package
openyoung package list                  # 列出已安装 (P0 ✅)
openyoung package search <query>         # 搜索 Package
openyoung package info <package>         # 查看 Package 信息

# 导入命令
openyoung import github <repo>          # 从 GitHub 导入
openyoung import <source> [args]        # 从其他源导入

# 评估命令 (实际可用)
openyoung eval list                     # 列出评估指标 (P0 ✅)
openyoung eval trend <agent>           # 查看评估趋势 (P0 ✅)
openyoung eval server                  # 启动评估 API 服务器
# 注意: eval run 命令当前不可用

# 配置命令
openyoung config list                   # 列出配置 (P0 ✅)
openyoung config get <key>            # 获取配置 (P0 ✅)
openyoung config set <key> <value>    # 设置配置

# 数据命令 (实际可用)
openyoung data runs                    # 列出运行记录 (P0 ✅)
openyoung data stats                   # 运行统计
openyoung data steps <run_id>          # 运行步骤
openyoung data dashboard               # 数据仪表板
openyoung data export                   # 导出数据
openyoung data license                  # 许可证管理
openyoung data team                     # 团队管理
openyoung data access                   # 访问日志
# 注意: data list 命令不存在，用 data runs 代替

# LLM 命令
openyoung llm list                      # 列出可用 LLM (P0 ✅)
openyoung llm use <provider>          # 设置默认 LLM
openyoung llm add <provider>           # 添加 LLM 提供商
openyoung llm remove <provider>        # 移除 LLM 提供商

# MCP 命令
openyoung mcp servers                   # 列出 MCP 服务器 (P0 ✅)
openyoung mcp start <server>          # 启动 MCP 服务器
openyoung mcp stop <server>            # 停止 MCP 服务器

# Memory 命令
openyoung memory list                   # 列出记忆 (P0 ✅)
openyoung memory search <query>       # 搜索记忆 (P0 ✅)
openyoung memory stats                 # 记忆统计 (P0 ✅)

# Skills 命令
openyoung skills list                   # 列出可用 Skills (P0 ✅)
openyoung skills create <name>         # 创建 Skill

# Channel 命令
openyoung channel list                  # 列出 Channel (P0 ✅)

# Source 命令
openyoung source list                   # 列出数据源 (P0 ✅)

# Subagent 命令
openyoung subagent list                 # 列出 Subagent
openyoung subagent create <name>       # 创建 Subagent

# Templates 命令
openyoung templates list                # 列出模板 (P0 ✅)

# Test 命令
openyoung test run                      # 运行测试
openyoung test coverage                 # 测试覆盖率

# 初始化命令
openyoung init                          # 初始化项目
```

> 📝 **测试状态标注**: (P0 ✅) 表示已通过 P0 测试用例

#### 命令行选项

```bash
# 全局选项
openyoung --help                        # 显示帮助
openyoung --version                    # 显示版本
openyoung --verbose                     # 详细输出
openyoung --config <path>              # 指定配置文件

# Run 命令选项
openyoung run <agent> <task>           # 运行任务
  --model, -m <model>                  # 指定模型
  --temperature, -t <temp>             # 设置温度
  --max-tokens <tokens>                # 最大 Token 数
  --sandbox                            # 启用沙箱
  --sandbox-pool                       # 启用沙箱池

# Agent 命令选项
openyoung agent list
  --all                                # 显示所有
  --badges                             # 显示徽章
  --stats                              # 显示统计

# Eval 命令选项
openyoung eval trend <agent>
  --metric, -m <metric>               # 指定评估指标

# Config 命令选项
openyoung config list
  --category <cat>                    # 分类显示

# Memory 命令选项
openyoung memory list
  --type <type>                       # 分类显示
  --page <num>                        # 分页
  --size <num>                        # 每页数量
```

### 5.3 命令分组结构

```
openyoung
├── run                 # 运行 Agent
├── agent               # Agent 管理
├── package             # Package 管理
├── install             # 安装 Package
├── import              # 导入
├── eval                # 评估
├── config              # 配置
├── data                # 数据
├── llm                 # LLM
├── mcp                 # MCP 服务器
├── memory              # 记忆
├── skills              # 技能
├── channel             # 通道
├── source              # 数据源
├── subagent            # 子代理
├── templates           # 模板
├── test                # 测试
└── init                # 初始化
```

### 5.4 AI Docker 沙箱集成

OpenYoung 内置 AI Docker 沙箱执行环境，为 AI Agent 提供安全可控的代码执行能力。

#### 沙箱配置选项

```bash
# 启用沙箱执行
openyoung run <agent> <task> --sandbox

# 配置沙箱参数
openyoung run <agent> <task>
  --sandbox                        # 启用沙箱
  --max-memory <MB>               # 最大内存 (默认 512MB)
  --max-time <seconds>            # 最大执行时间 (默认 300s)
  --allow-network                  # 允许网络访问

# 启用沙箱池 (自动扩缩容)
openyoung run <agent> <task> --sandbox-pool
  --min-instances <num>           # 最小实例数 (默认 2)
  --max-instances <num>          # 最大实例数 (默认 10)
  --idle-timeout <seconds>       # 空闲超时 (默认 300s)
```

#### 沙箱池状态

```bash
# 查看沙箱池状态
openyoung runtime status

# 列出活跃实例
openyoung runtime instances

# 查看实例统计
openyoung runtime stats
```

#### 编程式使用

```python
from src.agents import YoungAgent

# 启用沙箱
agent = YoungAgent(config)
agent.enable_sandbox(
    max_memory_mb=512,
    max_execution_time_seconds=300,
    allow_network=False,
)

# 启用沙箱池
agent.enable_sandbox_pool(
    min_size=2,
    max_size=10,
)
```

## 6. 文件结构

```
openyoung/
├── cli/
│   ├── __init__.py
│   ├── main.py              # CLI 入口
│   ├── commands/
│   │   ├── __init__.py
│   │   ├── run.py          # run 命令
│   │   ├── agent.py        # agent 命令
│   │   ├── package.py      # package 命令
│   │   └── config.py       # config 命令
│   └── utils.py
│
├── agents/                   # Agent 配置目录
│   ├── default.yaml        # 默认 Agent
│   ├── code-agent.yaml     # 代码 Agent
│   └── ...
│
├── packages/               # 已安装 Packages
│   └── ...
│
└── config.yaml             # 全局配置
```

## 7. 执行流程图

```
┌─────────────────────────────────────────────────────────┐
│                  openyoung run default                   │
│                    "写一个排序算法"                       │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                    AgentLoader                           │
│  1. 查找 default.yaml                                   │
│  2. 解析配置                                           │
│  3. 加载 dependencies                                  │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                 PackageManager                           │
│  1. 解析 dependencies                                  │
│  2. 安装缺失 packages                                  │
│  3. 加载 SKILL.md                                     │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                    YoungAgent                           │
│  1. 初始化 Model Client                                │
│  2. 加载 Skills                                        │
│  3. 配置 Flow                                          │
│  4. 设置 Evaluation                                     │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                    Execution                            │
│  1. pre_process (Flow Skill)                          │
│  2. Agent 执行                                         │
│  3. post_process (Flow Skill)                         │
│  4. Evaluation                                         │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
                    输出结果
```

## 8. 测试结果 (2026-03-09)

### 8.1 P0 测试通过的命令

| 命令组 | 命令 | 状态 |
|--------|------|------|
| **agent** | list | ✅ |
| | info | ✅ |
| | search | ✅ |
| | compare | ✅ |
| **config** | list | ✅ |
| | get | ✅ |
| **memory** | list | ✅ |
| | search | ✅ |
| | stats | ✅ |
| **eval** | list | ✅ |
| | trend | ✅ |
| **llm** | list | ✅ |
| **mcp** | servers | ✅ |
| **skills** | list | ✅ |
| **package** | list | ✅ |
| **source** | list | ✅ |
| **channel** | list | ✅ |
| **run** | default "task" | ✅ |

### 8.2 已修复的问题

1. **EvaluationHub.get_trend()** - 方法重复定义导致 CLI 调用失败，已重命名重复方法
2. **MCP servers 显示** - 已修复同时读取 mcp.json 和 package.yaml，现在正确显示 10 个服务器

### 8.3 已知限制

| 命令 | 状态 | 说明 |
|------|------|------|
| eval run | ❌ | 命令不存在 |
| data list | ❌ | 命令不存在，用 data runs 代替 |
| memory search | ⚠️ | 需要 API 密钥才能返回语义搜索结果 |
| eval server | ℹ️ | 启动 REST API 服务器 |

### 8.4 测试覆盖率目标

| 模块 | 目标覆盖率 | 实际测试数 |
|------|-----------|-----------|
| run 命令 | 90% | 1/21 |
| agent 命令 | 85% | 4/18 |
| config 命令 | 90% | 2/6 |
| memory 命令 | 85% | 3/6 |
| eval 命令 | 85% | 2/7 |
| llm 命令 | 80% | 1/5 |
| mcp 命令 | 75% | 1/2 |

---

## 附录：版本历史

| 日期 | 版本 | 说明 |
|------|------|------|
| 2026-03-09 | 1.0.0 | 初始版本，82 个测试用例 |
| 2026-03-09 | 1.0.1 | 更新测试结果，添加 P0 通过标记 |

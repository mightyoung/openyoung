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

### 5.2 完整命令列表

```bash
# Agent 命令
openyoung run <agent> [task]              # 运行 Agent
openyoung agent list                       # 列出可用 Agent
openyoung agent info <agent>              # 查看 Agent 信息
openyoung agent create <name>             # 创建新 Agent
openyoung agent validate <agent>          # 验证配置

# Package 命令
openyoung install <package>               # 安装 Package
openyoung package list                    # 列出已安装
openyoung package search <query>          # 搜索 Package
openyoung package info <package>          # 查看 Package 信息
openyoung package uninstall <package>      # 卸载
openyoung package update [package]        # 更新

# 配置命令
openyoung config get <key>                # 获取配置
openyoung config set <key> <value>       # 设置配置
openyoung config list                     # 列出配置

# 开发命令
openyoung dev start                       # 启动开发模式
openyoung dev test                        # 运行测试
openyoung dev build                       # 构建
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

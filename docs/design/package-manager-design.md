#VT|# Mightyoung Package Manager 设计
#KM|
#BK|> 版本: 1.0.1
#BX|> 更新日期: 2026-03-07
#BT|

> **重要更新 (2026-03-07)**: 包管理相关功能已迁移至 `src/hub/` 模块，保留 `src/package_manager/` 作为向后兼容导入。

---

## 1. 概述

Package Manager 是 Mightyoung 的**包管理核心**，负责包的安装、卸载、依赖解析、版本管理等。

设计原则：
- **零外部依赖** - SQLite + 文件系统，开箱即用
- **本地优先** - 默认本地存储，支持 GitHub 安装
- **组织隔离** - 命名空间支持，避免冲突
- **可验证** - SHA256 校验和，确保包完整性
- **Source 支持** - 可添加可信仓库作为包源
- **进化兼容** - 支持 Evolver 改进的 Skill 存储与合并

---

## 2. Package 架构

### 2.1 概念定义

Package 是包含**共性元信息** + **特性数据**的目录：

```
┌─────────────────────────────────────────────────┐
│              Package (目录)                       │
│  ┌─────────────────────────────────────────┐   │
│  │ package.yaml (共性元信息)                  │   │
│  │ - name, version, type                    │   │
│  │ - 依赖、校验和、入口                      │   │
│  └─────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────┐   │
│  │ 特性数据 (可选多个)                        │   │
│  │ - skill/        (Anthropic SKILL.md)   │   │
│  │ - mcp/          (MCP Server 结构)      │   │
│  │ - evaluation/   (评估规则)              │   │
│  │ - dataset/      (数据集)                 │   │
│  │ - capsule/     (OpenClaw GEP)           │   │
│  └─────────────────────────────────────────┘   │
└─────────────────────────────────────────────────┘
```

### 2.2 包类型

| 类型 | 说明 | 示例 |
|------|------|------|
| **skill** | Skill 包 | `@legal/contract-skills` |
| **mcp** | MCP 服务包 | `@github/mcp-server` |
| **evaluation** | 评估规则包 | `@bid/compliance-rules` |
| **dataset** | 数据集包 | `@medical/diagnosis-dataset` |
| **capsule** | Capsule 包 | `@patterns/code-review-capsule` |
| **hybrid** | 混合类型包 | `@org/multi-capability` |

---

## 3. Package 格式

### 3.1 package.yaml 共性格式

```yaml
# package.yaml - 所有 Package 的共性要求
name: "@org/my-package"
version: "1.0.0"

# Package 类型 (决定特性组合)
type: skill | mcp | evaluation | dataset | capsule | hybrid

description: "Package description"
repository: "https://github.com/owner/repo"
license: "MIT"

# 入口点
entry: "./skill.md"          # 主要入口

# 依赖
dependencies:
  "@other/pkg": "^2.0.0"

# 校验
checksum: "sha256:xxx"

# 元数据
metadata:
  author: "name"
  tags: ["ai", "agent"]
  created: "2026-03-01"
```

### 3.2 目录结构

```
@org-my-package/
├── package.yaml              # 共性要求 (必须)
├── skill/                   # Skill 特性 (可选)
│   └── SKILL.md             # Anthropic 标准
├── mcp/                     # MCP 特性 (可选)
│   ├── package.json          # npm 包
│   ├── .mcp.json           # MCP 配置
│   └── src/
│       └── server.py
├── evaluation/              # 评估特性 (可选)
│   └── rules.yaml
├── dataset/                 # 数据集特性 (可选)
│   └── data.yaml
└── capsule/                 # Capsule 特性 (可选)
    └── gene.yaml
```

### 3.3 特性配置

#### Skill 特性配置

```yaml
# package.yaml 中
type: skill
entry: "./skill/SKILL.md"

skill:
  # SKILL.md YAML frontmatter 兼容
  name: "my-skill"                    # kebab-case
  description: "What this skill does"
  disable_model_invocation: false
  allowed_tools:                       # 可选：限制工具
    - "bash"
    - "read"
  # 目录结构兼容
  paths:
    scripts: "./skill/scripts"        # 可执行脚本
    references: "./skill/references"  # 参考文档
    assets: "./skill/assets"         # 静态资源
```

#### MCP 特性配置

```yaml
# package.yaml 中
type: mcp
entry: "./mcp"

mcp:
  # .mcp.json 兼容
  server_type: local|remote           # 服务类型
  command: ["npx", "-y", "@org/mcp-server"]  # 本地启动命令
  args: ["--port", "8080"]
  env:                                 # 环境变量
    API_KEY: "${API_KEY}"

  # 远程服务配置
  url: "https://api.example.com/mcp"  # 远程服务地址
  headers:                             # 请求头
    Authorization: "Bearer ${TOKEN}"

  # MCP 能力声明 (可选，用于注册发现)
  capabilities:
    tools: true
    resources: true
    prompts: true
```

---

## 4. 版本策略（增强版 Cargo）

### 4.1 版本表达式

| 表达式 | 含义 | 示例 |
|--------|------|------|
| `*` | 任意版本 | `*` |
| `^` | 兼容版本 | `^1.2.3` → `>=1.2.3 <2.0.0` |
| `~` | 补丁兼容 | `~1.2.3` → `>=1.2.3 <1.3.0` |
| `=` | 精确版本 | `=1.2.3` |
| `>` `<` `>=` `<=` | 范围比较 | `>=1.0 <2.0` |
| `\|\|` | 或组合 | `^1.0 \|\| ^2.0` |

### 4.2 预发布版本

- 支持预发布版本：`1.0.0-alpha`, `1.0.0-beta.1`
- 排序规则：`1.0.0-alpha < 1.0.0-alpha.1 < 1.0.0-beta < 1.0.0`
- 预发布版本不满足稳定版约束（如 `^1.0.0` 不匹配 `1.0.0-alpha`）

---

## 5. 依赖解析

### 5.1 SAT 精确求解（参考 Cargo/uv）

- 使用 SAT 求解器找到满足所有约束的版本组合
- 冲突检测：无法解决时，清晰报告冲突来源
- 依赖裁剪：移除未使用的传递依赖

### 5.2 冲突处理（参考 Cargo）

```yaml
# 解决冲突示例
dependencies:
  "@org/skill": "^1.0.0"
  "@other/skill":
    version: "^2.0.0"
    alias: "skill-v2"  # 使用别名避免冲突
```

错误示例：
```
error: multiple packages named "skill" in dependency graph
help: use `alias` to distinguish them
```

---

## 6. 包验证

### 6.1 校验和机制（参考 npm/Cargo）

```yaml
# lock.yaml 示例
packages:
  "@org/skill":
    version: "1.2.0"
    source: "gh:owner/repo"
    checksum: "sha256:abc123..."
    dependencies:
      - "@other/pkg": "^2.0.0"
```

---

## 7. Source 系统（参考 Claude Code Market）

### 7.1 概念

| 概念 | 说明 |
|------|------|
| **Source** | 可信包仓库，可从其中浏览和安装包 |
| **本地 Source** | 本地目录作为包源 |
| **GitHub Source** | GitHub 仓库作为包源 |

### 7.2 Source 配置格式

```yaml
# .mightyoung/sources.yaml
sources:
  - name: "my-market"
    type: "local"
    path: "./my-market"

  - name: "github-skills"
    type: "github"
    repo: "owner/repo"
    path: "packages"        # 可选：子目录
    auth:                   # 可选认证
      type: "token"
      env: "GITHUB_TOKEN"
```

### 7.3 Source 导出格式

导出为本地 Source：
```
my-market/
├── source.yaml           # Source 元信息
├── packages/
│   ├── @org/
│   │   └── skill-a/
│   │       └── package.yaml
│   └── @local/
│       └── my-skill/
│           └── package.yaml
└── README.md
```

```yaml
# source.yaml
name: "my-market"
version: "1.0.0"
description: "My custom market"
author: "user"
packages:
  - "@org/skill-a"
  - "@local/my-skill"
```

### 7.4 查找顺序

```
1. 本地包目录 (.mightyoung/packages/)
2. 进化版本 (agents/my-agent/evolved/) - 最高优先级
3. Source 列表（按添加顺序）
   - 本地 Source
   - GitHub Source
```

### 7.5 冲突处理

- Source 间不校验包冲突
- 安装到本地时，按 Package Manager 冲突规则处理

---

## 8. 存储结构

```
项目目录/
├── .mightyoung/
│   ├── sources.yaml           # Source 配置
│   ├── packages/              # 已安装包（只读）
│   ├── evolved/               # 进化后的包（全局）
│   ├── cache/
│   ├── locks/
│   └── config.yaml
│
└── agents/
    └── my-agent/
        ├── mightyoung.yaml   # Agent 定义
        ├── lock.yaml        # Agent 级锁定
        ├── evolved/         # 进化后的 Skill（Agent级）
        │   └── @org/
        │       └── skill-a/
        │           └── skill.md
        └── merge_history/  # 合并历史
            └── skill-a/
                └── 2026-02-28_merge.yaml
```

---

## 9. CLI 命令

### 9.1 Package Create（创建）

将各种标准格式转换为标准 Package：

```bash
# 从 Anthropic Skill 格式创建
mightyoung package create ./my-skill --from skill

# 从 MCP Server 格式创建
mightyoung package create ./mcp-server --from mcp

# 从目录创建 (自动检测类型)
mightyoung package create ./my-package

# 从 GitHub 创建
mightyoung package create gh:owner/repo --from mcp

# 创建空 Package
mightyoung package create ./new-package --template hybrid

# 指定名称
mightyoung package create ./skill-folder --from skill --name "@org/my-skill"
```

**create 命令详细：**

```bash
mightyoung package create <source> [options]

选项:
  --from skill|mcp|evaluation|dataset|capsule|auto
                                      # 源格式类型 (auto=自动检测)
  --name <name>                      # Package 名称
  --type skill|mcp|evaluation|dataset|capsule|hybrid
                                      # Package 类型
  --output <path>                    # 输出路径
  --template <name>                  # 使用模板
  --force                            # 覆盖已存在的 Package
```

**自动检测逻辑：**

| 检测条件 | 推断类型 |
|----------|----------|
| 存在 `SKILL.md` | skill |
| 存在 `.mcp.json` | mcp |
| 存在 `package.json` + `.mcp.json` | mcp |
| 存在 `rules.yaml` | evaluation |
| 存在 `gene.yaml` | capsule |
| 都不是 | hybrid |

### 9.2 Package Publish（发布）

```bash
# 发布到默认 Source
mightyoung package publish @org/my-skill

# 发布到 Source
mightyoung package publish @org/my-skill --to source

# 发布到 GitHub
mightyoung package publish @org/my-skill --to github --repo owner/my-skill-repo

# 发布 MCP 到 npm
mightyoung package publish @org/mcp-server --to npm --access public

# 发布到企业仓库
mightyoung package publish @org/my-pkg --to custom --url https://registry.internal.com
```

**publish 命令详细：**

```bash
mightyoung package publish [package] [options]

参数:
  package              Package 名称 (默认: 当前目录)

选项:
  --to source|github|npm|custom
                      发布目标 (默认: source)
  --repo <owner/repo> GitHub 仓库 (--to github 时必填)
  --registry <url>    自定义仓库地址 (--to custom 时必填)
  --access public|private
                      发布可见性 (npm 时使用)
  --token <token>    认证令牌
```

### 9.3 Package Export（导出）

将 Package 导出为各种标准格式：

```bash
# 导出为 Anthropic Skill 格式
mightyoung package export @org/my-skill --to skill

# 导出为 MCP Server 结构
mightyoung package export @org/my-mcp --to mcp

# 导出为 npm 包
mightyoung package export @org/my-mcp --to npm

# 导出为 Source
mightyoung package export @org/my-package --to source

# 导出所有特性
mightyoung package export @org/my-package --all
```

**export 命令详细：**

```bash
mightyoung package export <package> [options]

参数:
  package              Package 名称 (默认: 当前目录)

选项:
  --to skill|mcp|npm|source|all
                      导出格式 (默认: skill)
  --output <path>     输出目录 (默认: ./exports/{package})
  --overwrite         覆盖已存在的文件
```

### 9.4 Package 管理

```bash
# 安装
mightyoung package install <name>[@version]           # 从远程安装
mightyoung package install ./path/to/package          # 本地安装
mightyoung package install gh:owner/repo             # 从 GitHub 安装
mightyoung package install @source:pkg               # 从指定 Source 安装

# 卸载
mightyoung package uninstall <name>                  # 卸载（仅移除直接依赖）
mightyoung package prune                            # 清理未使用的传递依赖

# 管理
mightyoung package list                            # 列出已安装
mightyoung package outdated                        # 检查更新
mightyoung package upgrade <name>                 # 升级

# 锁定
mightyoung package lock                            # 生成 lock.yaml
```

### 9.5 Source 管理

```bash
# 添加 Source
mightyoung source add <path>              # 添加本地 Source
mightyoung source add gh:owner/repo        # 添加 GitHub Source

# Source 管理
mightyoung source list                     # 列出所有 Source
mightyoung source remove <name>            # 移除 Source
mightyoung source update <name>            # 拉取最新包列表

# 浏览搜索
mightyoung source browse <name>            # 浏览 Source 中的包
mightyoung source search <query>           # 搜索所有 Source
```

---

## 10. Agent 与 Package 关系

### 10.1 核心原则

1. **解耦** - Package 是独立实体，Agent 按需引用
2. **共享** - Package 可被多个 Agent 共享
3. **锁定** - lock.yaml 锁定原始版本
4. **进化优先** - 同名包优先加载进化版本
5. **自动检查** - 安装/升级时自动检查兼容性
6. **多版本** - 支持同一 Package 不同版本共存

### 10.2 协同流程

```
开发阶段：
1. Agent 定义 → mightyoung.yaml
2. 首次启动 → 检测新包依赖 → 提示安装
3. 安装包 → .mightyoung/packages/
4. 生成 lock.yaml → agents/my-agent/lock.yaml

运行阶段：
1. Agent 启动 → 读取 lock.yaml
2. 加载顺序：evolved/ → packages/
3. 执行任务

更新阶段：
1. 检测原始包更新
2. 如有进化版本 → 提示合并策略
3. 用户选择后更新
```

---

## 11. Evolver 兼容设计

### 11.1 冲突问题

| 组件 | 行为 | 冲突点 |
|------|------|--------|
| **Package Manager** | lock.yaml 锁定版本，从 .mightyoung/packages/ 加载 | 只读 |
| **Evolver** | 运行时改进 Skill | 可写，无持久化 |

### 11.2 解决方案：分层存储 + 加载顺序

```
加载顺序（优先级从高到低）：

1. agents/my-agent/evolved/   # 进化后的 Skill（Agent级）
2. .mightyoung/evolved/     # 进化后的 Skill（全局）
3. .mightyoung/packages/    # 安装的原始包（只读）
```

### 11.3 合并策略

当原始 Skill 升级时，检测进化版本并进行三路合并：

| 策略 | 说明 | 适用场景 |
|------|------|----------|
| **自动合并** | 无冲突时自动合并 | 简单改动 |
| **LLM 合并** | AI 智能解决冲突 | 复杂语义修改 |
| **手动合并** | 用户介入解决 | 高风险冲突 |

### 11.4 用户交互

```
检测到 Skill "@org/skill-a" 有新版本 v1.2.0

当前使用：进化版 v1.1.0 (本地修改)

请选择：
[A] 自动合并 (推荐)
    - 升级版新功能 + 进化版修改 → 智能合并

[B] 保留进化版
    - 继续使用本地进化版
    - 忽略升级

[C] 覆盖为升级版
    - 丢弃进化版
    - 使用升级版 v1.2.0

[D] 手动查看差异
    - 查看详细 diff
```

### 11.5 LLM 合并提示词

```python
MERGE_PROMPT = """
你是一个专业的代码/文本合并助手。请帮我合并两个版本的 Skill。

原始版本 (升级版):
---
{upgrade_content}
---

进化版本 (本地修改):
---
{evolved_content}
---

请：
1. 保留升级版的新功能
2. 保留进化版的优化
3. 解决冲突，保留最有价值的部分
4. 输出合并后的完整内容

如果无法确定，优先保留进化版的修改。
"""
```

### 11.6 merge_history 格式

```yaml
version: "1.0"
skill_name: "@org/skill-a"

merges:
  - timestamp: "2026-02-28T10:00:00Z"
    base_version: "1.1.0"
    upgrade_version: "1.2.0"
    evolved_version: "1.1.0-evolved"
    strategy: "llm_merge"  # auto | llm | manual
    result: "merged"
    diff_url: "./2026-02-28_diff.md"
```

---

## 12. lock.yaml 格式

```yaml
# lock.yaml
version: "1.0"

metadata:
  generated_at: "2026-02-28T10:00:00Z"
  generator: "mightyoung/1.0.0"

packages:
  "@org/skill":
    version: "1.2.0"
    source:
      type: "github"
      repo: "owner/skill"
      path: "packages/skill"
    checksum: "sha256:abc123..."
    dependencies:
      - name: "@other/pkg"
        version: "2.1.0"

  "@other/pkg":
    version: "2.1.0"
    source:
      type: "local"
    checksum: "sha256:def456..."

  # 进化版本记录
  evolved:
    "@org/skill":
      version: "1.1.0-evolved"
      base_version: "1.1.0"
      evolved_at: "2026-02-27T10:00:00Z"
```

---

## 13. 与 EvaluationCenter 关系

### 13.1 管控范围

Package Manager 管控 Evaluation 包的配置：

| 管控项 | 说明 |
|--------|------|
| **包版本** | Evaluation 包版本管理 |
| **依赖** | Evaluation 包依赖冲突解决 |
| **配置** | package.yaml 中的 evaluation 配置 |

### 13.2 使用逻辑独立

EvaluationCenter 的使用逻辑独立于 Package Manager：

| 独立项 | 说明 |
|--------|------|
| **评估器注册** | Center 内部评估器管理 |
| **注入策略** | 评估注入时机和方式 |
| **触发规则** | 何时触发评估 |

### 13.3 示例

```yaml
# package.yaml - Evaluation 包
name: "@eval/correctness"
version: "1.0.0"
type: evaluation
description: "Correctness evaluation rules"
entry: "./evaluation/rules.yaml"

evaluation:
  dimensions:
    - correctness
  thresholds:
    score: 0.8
```

PM 管控：包版本 `1.0.0`、依赖解析

Center 独立：如何使用这些配置（注入策略、触发规则）

---

## 14. 设计决策汇总

| 项目 | 方案 |
|------|------|
| 依赖解析 | SAT 精确求解 + Cargo 风格 |
| 查找顺序 | 进化版本 → 本地 → Source 列表 |
| 包验证 | SHA256 校验和 |
| 目录结构 | 嵌套 (共性 + 特性) |
| GitHub 格式 | Claude Code Market 风格 |
| 本地开发 | 默认本地 |
| 版本策略 | 增强版 Cargo（全部表达式 + 预发布） |
| 冲突处理 | 报错 + rename 别名 |
| 卸载行为 | 默认仅移除直接依赖 + prune 命令 |
| Source 认证 | 可配置，默认无认证 |
| Source 导出 | 可选导出部分（skills/datasets/evaluation） |
| 进化存储 | Agent 级 (`agents/my-agent/evolved/`) |
| 合并策略 | 三路合并 + LLM 智能合并 |
| Package 创建 | 支持外部格式转换 |
| Package 发布 | Source / GitHub / npm / 自定义仓库 |
| Package 导出 | Skill / MCP / npm / Source 格式 |

---

## 15. 参考实现

- **Cargo**: SAT 求解、依赖解析、lock 文件
- **uv**: 快速依赖解析、校验和
- **npm**: 包格式、package-lock
- **Claude Code Market**: Source 结构、导出导入
- **Anthropic SKILL.md**: Skill 格式标准
- **MCP Protocol**: MCP Server 标准
- **diff3**: 三路合并算法
- **LLMinus**: LLM 辅助合并冲突解决

---

## 16. Hub 模块架构 (2026-03-07)

### 16.1 模块迁移

为提高代码组织性，包管理相关功能已迁移至 `src/hub/` 目录：

```
src/hub/
├── hooks/       # HooksLoader - 生命周期钩子
├── intent/     # IntentAnalyzer - 意图分析
├── version/    # VersionManager - 版本管理
├── template/   # TemplateRegistry - 模板注册
├── mcp/        # MCPServerManager, MCPLoader
├── badge/      # BadgeSystem - 徽章系统
├── registry/   # AgentRegistry, SubAgentRegistry
├── io/         # AgentExporter, AgentImporter
├── evaluate/   # AgentEvaluator - 评估器
└── discover/   # AgentRetriever - 技能检索
```

### 16.2 向后兼容

保留原始导入路径确保向后兼容：

```python
# 新路径（推荐）
from src.hub.hooks import HooksLoader
from src.hub.mcp import MCPServerManager

# 旧路径（兼容）
from src.package_manager.hooks_loader import HooksLoader
from src.package_manager.mcp_manager import MCPServerManager
```

---

*本文档整合了 Skills、MCP、Evaluation、Dataset、Capsule 的包格式设计*

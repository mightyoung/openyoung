# OpenYoung 配置手册

> **版本**: 1.1.0
> **更新日期**: 2026-03-06

---

## 1. 配置概述

### 1.1 配置方式

OpenYoung 支持多种配置方式，优先级从高到低：

1. **环境变量** - 最高优先级
2. **命令行参数** - 次优先级
3. **配置文件** (YAML/JSON) - 中等优先级
4. **默认配置** - 最低优先级

### 1.2 配置目录结构

```
config/
├── default.yaml          # 默认配置
├── production.yaml      # 生产环境
├── development.yaml    # 开发环境
├── agent.yaml          # Agent 配置
├── flow.yaml          # 流程配置
└── skills/            # 技能配置
    ├── writing.yaml
    └── analysis.yaml
```

---

## 2. Agent 配置

### 2.1 基本配置

```yaml
# config/agent.yaml
agent:
  name: "my_agent"
  model: "gpt-4"
  temperature: 0.7
  max_tokens: 4096
  mode: "primary"  # primary | subagent | all

  # 可选配置
  system_prompt: |
    你是一个专业的 AI 助手。

  history_limit: 100
  timeout: 120
```

### 2.2 Skills 配置

```yaml
# Agent 技能配置
# 技能分为 always_skills（自动加载）和 skills（按需加载）

# Always Skills - Agent 启动时自动加载
always_skills:
  - self-improvement    # 自动记录错误、学习、持续改进
  - find-skills         # 智能发现 skills.sh 生态中的技能
  - summarize           # 智能摘要网页、文件、PDF、视频

# 按需 Skills - 任务触发时加载
skills:
  - github-import      # GitHub Agent 导入
  - coding-standards   # 编码规范
  - eval-planner      # 评估计划生成
```

### 2.2 权限配置

```yaml
permission:
  # 全局策略: allow | ask | deny
  _global: ask

  rules:
    # 规则1: 允许读取操作
    - tool_pattern: "read|glob|grep"
      action: allow

    # 规则2: 写操作需要确认
    - tool_pattern: "write|edit"
      action: ask
      params_pattern:
        force: false

    # 规则3: 危险操作拒绝
    - tool_pattern: "rm.*-rf|system.*admin"
      action: deny

    # 规则4: 特定文件保护
    - tool_pattern: "write"
      action: deny
      params_pattern:
        path: "/etc/*"

  confirm_message: "确定要执行此操作吗?"
```

### 2.3 SubAgent 配置

```yaml
subagents:
  - name: "explore"
    type: "explore"
    description: "快速探索代码库"
    permission:
      _global: allow

  - name: "builder"
    type: "builder"
    description: "构建和执行任务"
    permission:
      _global: allow

  - name: "reviewer"
    type: "reviewer"
    description: "代码审查"
    permission:
      _global: deny
      rules:
        - tool_pattern: "write|edit|bash"
          action: deny
```

---

## 3. 流程配置

### 3.1 顺序流配置

```yaml
flow:
  sequential:
    name: "dev_workflow"
    description: "开发工作流"
    steps:
      - action: "analyze"
        description: "分析需求"
        timeout: 60

      - action: "design"
        description: "设计架构"
        timeout: 120

      - action: "implement"
        description: "实现代码"
        timeout: 300

      - action: "test"
        description: "测试验证"
        timeout: 180

      - action: "review"
        description: "代码审查"
        timeout: 120

    on_error: "rollback"  # rollback | continue | stop
```

### 3.2 并行流配置

```yaml
flow:
  parallel:
    name: "data_pipeline"
    max_workers: 4

    tasks:
      - id: "download"
        description: "下载数据"

      - id: "process"
        description: "处理数据"

      - id: "upload"
        description: "上传结果"

    timeout: 300
    on_error: "cancel_all"  # cancel_all | wait_completion
```

### 3.3 条件流配置

```yaml
flow:
  conditional:
    name: "task_router"

    conditions:
      - pattern: ".*bug.*|.*fix.*"
        branch: "fix_bug"

      - pattern: ".*feature.*|.*add.*"
        branch: "add_feature"

      - pattern: ".*refactor.*|.*improve.*"
        branch: "refactor"

      - pattern: ".*docs?.*|.*document.*"
        branch: "update_docs"

    default_branch: "general_task"
```

### 3.4 循环流配置

```yaml
flow:
  loop:
    name: "retry_task"
    max_iterations: 5

    condition:
      type: "until_success"  # until_success | until_max | while_true

    body:
      action: "execute_task"
      timeout: 60

    on_complete:
      - action: "notify"
      - action: "log"
```

---

## 4. 记忆配置

### 4.1 自动记忆配置

```yaml
memory:
  auto_memory:
    # 最大记忆数量
    max_memories: 100

    # 重要性阈值 (0-1)
    importance_threshold: 0.5

    # 各层大小限制
    limits:
      working: 10
      session: 50
      persistent: 100

    # 清理策略
    cleanup:
      enabled: true
      interval: 3600  # 秒
      strategy: "lru"  # lru | fifo | importance
```

### 4.2 检查点配置

```yaml
checkpoint:
  enabled: true
  storage: "redis"  # redis | file | database

  redis:
    url: "redis://localhost:6379/0"
    prefix: "young:checkpoint:"

  file:
    path: "./checkpoints"
    max_size: 100MB

  # 自动检查点
  auto_checkpoint:
    enabled: true
    interval: 300  # 秒
    on_error: true
```

---

## 5. 评估配置

### 5.1 评估中心配置

```yaml
evaluation:
  hub:
    enabled: true

    # 默认指标
    metrics:
      - name: "accuracy"
        weight: 0.3
        threshold: 0.7

      - name: "coherence"
        weight: 0.2
        threshold: 0.6

      - name: "safety"
        weight: 0.3
        threshold: 0.9

      - name: "helpfulness"
        weight: 0.2
        threshold: 0.5

    # 评估缓存
    cache:
      enabled: true
      ttl: 3600
```

### 5.2 自定义指标

```yaml
custom_metrics:
  - name: "code_quality"
    type: "llm_judge"
    prompt: |
      评估以下代码质量 (1-10分):
      {{code}}

    criteria:
      - "可读性"
      - "性能"
      - "安全性"

  - name: "response_time"
    type: "threshold"
    threshold: 5.0  # 秒
```

---

## 6. 技能配置

### 6.1 技能管理器配置

```yaml
skills:
  manager:
    # 自动发现
    auto_discover:
      enabled: true
      paths:
        - "./skills"
        - "./src/skills"
        - "./packages"

    # 技能路径
    paths:
      - "/usr/local/share/young/skills"

    # 默认超时
    default_timeout: 60

    # 隔离执行
    isolation:
      enabled: true
      sandbox: "none"  # none | docker | subprocess
```

### 6.2 技能定义 (skill.yaml)

技能通过 YAML 文件定义，存放在 `src/skills/` 或 `packages/skill-*/` 目录：

```yaml
# src/skills/my-skill/skill.yaml
name: "my-skill"
description: |
  技能描述，当用户请求相关内容时自动触发
version: "1.0.0"
entry: "SKILL.md"  # 技能入口文件
tags:
  - utility
  - automation
always: false  # 是否作为 always_skills 加载
```

### 6.3 技能来源

| 来源 | 目录 | 用途 |
|------|------|------|
| 内置技能 | `src/skills/{skill_name}/` | Agent 内置技能 |
| 包技能 | `packages/skill-{name}/` | 可发布的技能包 |

### 6.4 技能加载优先级

1. **Always Skills** - 从 `src/skills/` 加载，Agent 启动时自动加载
2. **Regular Skills** - 从 `packages/` 加载，按需加载

---

## 7. MCP 配置

### 7.1 MCP 客户端配置

```yaml
mcp:
  client:
    # 默认超时
    timeout: 30

    # 重试配置
    retry:
      enabled: true
      max_attempts: 3
      backoff: "exponential"

    # 连接池
    pool:
      max_size: 10
      min_size: 2
```

### 7.2 MCP Server 配置

```yaml
mcp:
  servers:
    - name: "local"
      url: "http://localhost:8080"
      enabled: true

    - name: "openai"
      url: "https://api.openai.com/v1"
      api_key: "${OPENAI_API_KEY}"
      enabled: false

  # 工具映射
  mappings:
    local_search: "web_search"
    local_read: "file_read"
```

---

## 8. 演化配置

### 8.1 基因配置

```yaml
evolver:
  enabled: true

  # 演化参数
  evolution:
    population_size: 10
    generations: 5
    mutation_rate: 0.1
    crossover_rate: 0.7
    selection_strategy: "tournament"

  # 基因定义
  genes:
    - name: "intelligence"
      min: 0.0
      max: 1.0
      default: 0.7

    - name: "creativity"
      min: 0.0
      max: 1.0
      default: 0.5

    - name: "patience"
      min: 0.0
      max: 1.0
      default: 0.6

  # 胶囊配置
  capsules:
    storage: "file"
    path: "./capsules"
```

---

## 9. 数据中心配置

### 9.1 追踪配置

```yaml
datacenter:
  trace:
    enabled: true

    # 存储
    storage: "redis"  # redis | file | database

    redis:
      url: "redis://localhost:6379/1"
      prefix: "young:trace:"

    # 采样率
    sample_rate: 1.0  # 0-1

    # 保留时间
    retention: 604800  # 7天 (秒)
```

### 9.2 预算控制

```yaml
  budget:
    # Token 预算
    tokens:
      max_per_request: 10000
      max_per_session: 100000

    # 速率限制
    rate_limit:
      enabled: true
      requests_per_minute: 60
      requests_per_hour: 1000

    # 配额
    quota:
      daily_limit: 10000
      monthly_limit: 100000
```

### 9.3 模式检测

```yaml
  pattern_detector:
    enabled: true

    # 检测模式
    patterns:
      - name: "frequent_file_access"
        threshold: 10

      - name: "error_pattern"
        threshold: 5

    # 通知
    alert:
      enabled: true
      channels:
        - "log"
        - "webhook"
```

---

## 10. 日志配置

### 10.1 日志级别

```yaml
logging:
  level: "info"  # debug | info | warning | error | critical

  # 模块级别
  modules:
    "src.agents": "debug"
    "src.flow": "info"
    "src.memory": "warning"
```

### 10.2 日志输出

```yaml
  handlers:
    console:
      enabled: true
      format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    file:
      enabled: true
      path: "./logs/openyoung.log"
      max_size: 100MB
      backup_count: 10

    syslog:
      enabled: false
      address: "localhost:514"
      facility: "local0"
```

---

## 11. 环境变量

### 11.1 必需变量

| 变量名 | 说明 | 示例 |
|--------|------|------|
| `YOUNG_ENV` | 运行环境 | `production` |
| `YOUNG_SECRET_KEY` | 密钥 | `your-secret-key` |

### 11.2 可选变量

| 变量名 | 默认值 | 说明 |
|--------|---------|------|
| `YOUNG_HOST` | `0.0.0.0` | 监听地址 |
| `YOUNG_PORT` | `8000` | 监听端口 |
| `YOUNG_LOG_LEVEL` | `info` | 日志级别 |
| `YOUNG_CONFIG_PATH` | `./config` | 配置目录 |
| `YOUNG_DB_URL` | - | 数据库连接 |
| `YOUNG_REDIS_URL` | - | Redis 连接 |
| `YOUNG_OPENAI_API_KEY` | - | OpenAI API Key |

---

## 12. 完整配置示例

### 12.1 开发环境

```yaml
# config/development.yaml
environment: development

agent:
  name: "dev_agent"
  model: "gpt-4"
  mode: "primary"

permission:
  _global: allow

flow:
  sequential:
    name: "dev_flow"

memory:
  auto_memory:
    max_memories: 50

logging:
  level: "debug"
```

### 12.2 生产环境

```yaml
# config/production.yaml
environment: production

agent:
  name: "prod_agent"
  model: "gpt-4"
  mode: "primary"
  timeout: 120

permission:
  _global: ask
  rules:
    - tool_pattern: ".*"
      action: ask

flow:
  sequential:
    name: "prod_flow"
    on_error: "stop"

memory:
  auto_memory:
    max_memories: 100
  checkpoint:
    enabled: true
    storage: "redis"

evaluation:
  hub:
    enabled: true

mcp:
  servers:
    - name: "prod_mcp"
      url: "${MCP_SERVER_URL}"

logging:
  level: "info"
  handlers:
    file:
      enabled: true
      path: "/var/log/openyoung/openyoung.log"
```

---

## 13. 配置验证

### 13.1 验证命令

```bash
# 验证配置语法
python -m src.config.loader --validate config/production.yaml

# 测试配置加载
python -c "from src.config.loader import ConfigLoader; c = ConfigLoader().load_all(); print(c)"
```

### 13.2 配置模板

```bash
# 生成默认配置
python -m src.config init

# 生成指定环境配置
python -m src.config init --env production

# 列出所有配置项
python -m src.config list
```

---

## 14. 附录

### 14.1 配置项索引

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|---------|------|
| `agent.name` | string | - | Agent 名称 |
| `agent.model` | string | - | 模型名称 |
| `agent.temperature` | float | 0.7 | 温度参数 |
| `permission._global` | enum | ask | 全局权限策略 |
| `flow.sequential.steps` | array | [] | 步骤列表 |
| `memory.auto_memory.max_memories` | int | 100 | 最大记忆数 |
| `evaluation.hub.enabled` | bool | true | 启用评估 |
| `logging.level` | enum | info | 日志级别 |

### 14.2 常见问题

**Q: 如何查看当前配置?**
```bash
python -m src.config dump
```

**Q: 配置不生效?**
1. 检查环境变量优先级
2. 验证 YAML 语法
3. 确认配置文件路径

**Q: 如何覆盖特定配置?**
```bash
# 使用环境变量
export YOUNG_AGENT_NAME=custom_name
```

PP|
---

## 15. LLM Provider 配置

### 15.1 支持的 Provider

OpenYoung 支持多种 LLM Provider：

| Provider | 模型 | Base URL |
|----------|------|----------|
| DeepSeek | deepseek-chat, deepseek-coder | https://api.deepseek.com |
| Moonshot | moonshot-v1-8k, moonshot-v1-32k | https://api.moonshot.cn |
| Qwen | qwen-turbo, qwen-plus | https://dashscope.aliyuncs.com |
| GLM | glm-4, glm-4-flash | https://open.bigmodel.cn |

### 15.2 Provider 配置示例

```yaml
# config/llm.yaml
llm:
  providers:
    - name: "deepseek"
      provider_type: "deepseek"
      base_url: "https://api.deepseek.com"
      api_key: "${DEEPSEEK_API_KEY}"
      enabled: true
      models:
        - "deepseek-chat"
        - "deepseek-coder"
      default: true

    - name: "moonshot"
      provider_type: "moonshot"
      base_url: "https://api.moonshot.cn"
      api_key: "${MOONSHOT_API_KEY}"
      enabled: true
      models:
        - "moonshot-v1-8k"
```

### 15.3 环境变量配置

```bash
# DeepSeek
export DEEPSEEK_API_KEY="sk-xxxx"

# Moonshot
export MOONSHOT_API_KEY="xxxx"

# Qwen (DashScope)
export DASHSCOPE_API_KEY="xxxx"

# GLM
export ZHIPU_API_KEY="xxxx"
```

### 15.4 CLI 管理

```bash
# 列出 Provider
openyoung llm list

# 添加 Provider
openyoung llm add deepseek --api-key sk-xxxx --default

# 查看详情
openyoung llm info deepseek

# 设置默认
openyoung llm use deepseek

# 移除
openyoung llm remove deepseek
```

### 15.5 配置验证

```python
from src.cli.main import AgentLoader
from src.core.types import AgentConfig, AgentMode

loader = AgentLoader()

# 验证配置
config = AgentConfig(
    name="test",
    model="deepseek-chat",
    mode=AgentMode.PRIMARY,
    temperature=0.7
)

is_valid, error = loader.validate_config(config)
print(f"Valid: {is_valid}, Error: {error}")

# 验证 Agent 文件
is_valid, error = loader.validate_agent_file(Path("agents/my_agent.yaml"))
```

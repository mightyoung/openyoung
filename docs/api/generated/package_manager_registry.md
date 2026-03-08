AgentRegistry - 轻量级 Agent 注册中心
基于文件夹 + YAML 配置，使用 pip 管理依赖

## Classes

### `AgentSpec`

Agent 规格定义

### `AgentRegistry`

轻量级 Agent 注册中心

目录结构:
packages/
├── agent-coder/
│   ├── pyproject.toml      # pip 依赖
│   ├── agent.yaml          # Agent 配置
│   └── src/
└── agent-reviewer/
    ├── pyproject.toml
    ├── agent.yaml
    └── src/

**Methods:**
- `discover_agents`
- `get_agent`
- `list_agents`
- `index_agent`
- `index_all_agents`
- `get_agent_dict`
- `track_usage`
- `get_usage_stats`
- `install_agent`
- `install_all`
- `create_agent_template`
- `export_registry`
- `save_registry`

## Functions

### `discover_agents()`

扫描并发现所有 Agent

### `get_agent()`

获取指定 Agent

### `list_agents()`

列出所有可用 Agent

### `index_agent()`

索引 Agent 到向量存储

Args:
    agent_name: Agent 名称

Returns:
    bool: 索引是否成功

### `index_all_agents()`

索引所有 Agent

Returns:
    int: 成功索引的数量

### `get_agent_dict()`

获取 Agent 字典格式（包含所有字段）

### `track_usage()`

追踪 agent 使用

Args:
    agent_name: Agent 名称

Returns:
    bool: 是否成功记录

### `get_usage_stats()`

获取使用统计

Args:
    limit: 返回数量

Returns:
    List[Dict]: 使用统计列表

### `install_agent()`

安装 Agent 依赖 (使用 pip)

### `install_all()`

安装所有 Agent 依赖

### `create_agent_template()`

创建 Agent 模板

### `export_registry()`

导出注册表 JSON

### `save_registry()`

保存注册表到文件

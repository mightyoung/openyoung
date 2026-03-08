DataStore - 统一数据访问入口
基于 SQLAlchemy 实现统一的数据访问层

## Classes

### `EntityType`

实体类型

### `Entity`

统一实体表

### `Version`

版本历史表

### `DataStore`

统一数据访问入口

**Methods:**
- `save_agent`
- `get_agent`
- `list_agents`
- `delete_agent`
- `save_run`
- `get_run`
- `list_runs`
- `save_checkpoint`
- `get_checkpoint`
- `list_checkpoints`
- `save_workspace`
- `get_workspace`
- `save_with_transaction`
- `save_version`
- `get_version`
- `list_versions`
- `get_stats`

## Functions

### `get_data_store()`

获取 DataStore 实例

### `save_agent()`

保存 Agent

### `get_agent()`

获取 Agent

### `list_agents()`

列出所有 Agents

### `delete_agent()`

删除 Agent

### `save_run()`

保存运行记录

### `get_run()`

获取运行记录

### `list_runs()`

列出运行记录

### `save_checkpoint()`

保存 Checkpoint

### `get_checkpoint()`

获取 Checkpoint

### `list_checkpoints()`

列出 Checkpoints

### `save_workspace()`

保存 Workspace

### `get_workspace()`

获取 Workspace

### `save_with_transaction()`

原子性执行多个操作

### `save_version()`

保存版本

### `get_version()`

获取版本

### `list_versions()`

列出版本历史

### `get_stats()`

获取统计信息

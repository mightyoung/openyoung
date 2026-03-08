DataExporter - 数据导出
支持多种格式导出，带授权信息
统一数据源：只从 runs.db 读取

## Classes

### `DataExporter`

数据导出器

**Methods:**
- `db_path`
- `export_runs`
- `export_steps`
- `export_agents`
- `export_with_license`
- `export_full`

## Functions

### `get_data_exporter()`

获取数据导出器

### `db_path()`

### `export_runs()`

导出运行记录（只从 runs.db 读取）

### `export_steps()`

导出步骤记录

### `export_agents()`

导出 Agent 数据（从 runs.db 查询唯一 agent_id）

### `export_with_license()`

带授权信息导出

### `export_full()`

导出所有数据

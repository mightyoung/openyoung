RunTracker - Agent 运行追踪
记录 Run 级别数据采集
使用 BaseStorage 基类

## Classes

### `RunRecord`

运行记录

**Methods:**
- `to_dict`

### `RunTracker`

运行追踪器

**Methods:**
- `start_run`
- `complete_run`
- `fail_run`
- `get_run`
- `list_runs`
- `get_stats`

## Functions

### `get_run_tracker()`

获取运行追踪器

### `to_dict()`

转换为字典

### `start_run()`

开始追踪一个运行

### `complete_run()`

完成运行追踪

### `fail_run()`

标记运行失败

### `get_run()`

获取运行记录

### `list_runs()`

列出运行记录

### `get_stats()`

获取统计数据

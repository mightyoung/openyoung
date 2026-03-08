Checkpoint - 标准 Checkpoint 接口
LangGraph 风格: SqliteSaver, CheckpointSaver Protocol

## Classes

### `CheckpointSaver`

标准 Checkpoint 接口 - LangGraph 风格

**Methods:**
- `get`
- `put`
- `list`
- `delete`

### `Checkpoint`

检查点

### `SqliteCheckpointSaver`

SQLite 检查点存储 - LangGraph 风格

**Methods:**
- `get`
- `put`
- `list`
- `delete`
- `get_by_id`
- `get_thread_count`

## Functions

### `get_checkpoint_saver()`

获取检查点存储

### `get()`

获取检查点

### `put()`

保存检查点

### `list()`

列出检查点

### `delete()`

删除检查点

### `get()`

获取最新检查点

### `put()`

保存检查点

### `list()`

列出检查点

### `delete()`

删除检查点

### `get_by_id()`

根据 ID 获取检查点

### `get_thread_count()`

获取线程的检查点数量

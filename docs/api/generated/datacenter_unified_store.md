UnifiedStore - 统一存储层

基于 BaseStorage 实现 ExecutionRecord 的统一存储
支持 CRUD 操作和跨表查询

## Classes

### `UnifiedStore`

统一存储层 - 执行记录

**Methods:**
- `save`
- `get`
- `get_by_session`
- `get_by_run`
- `list_recent`
- `list_by_status`
- `update_status`
- `delete`
- `count`
- `get_stats`

## Functions

### `get_unified_store()`

获取统一存储实例

### `save()`

保存执行记录

### `get()`

根据 ID 获取执行记录

### `get_by_session()`

根据 session_id 查询执行记录

### `get_by_run()`

根据 run_id 查询执行记录（包括关联的 step）

### `list_recent()`

列出最近的执行记录

### `list_by_status()`

根据状态查询执行记录

### `update_status()`

更新执行状态

### `delete()`

删除执行记录

### `count()`

统计执行记录数量

### `get_stats()`

获取统计信息

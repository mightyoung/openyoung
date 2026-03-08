Cached DataStore - 带缓存的数据访问层
使用 cachetools 实现 LRU 缓存

## Classes

### `CachedDataStore`

带缓存的 DataStore

**Methods:**
- `get_agent`
- `save_agent`
- `delete_agent`
- `get_run`
- `save_run`
- `get_checkpoint`
- `save_checkpoint`
- `get_workspace`
- `save_workspace`
- `clear_cache`
- `get_cache_stats`

## Functions

### `get_cached_store()`

获取带缓存的 DataStore

### `get_agent()`

获取 Agent (带缓存)

### `save_agent()`

保存 Agent (使缓存失效)

### `delete_agent()`

删除 Agent (使缓存失效)

### `get_run()`

获取 Run (带缓存)

### `save_run()`

保存 Run (使缓存失效)

### `get_checkpoint()`

获取 Checkpoint (带缓存)

### `save_checkpoint()`

保存 Checkpoint (使缓存失效)

### `get_workspace()`

获取 Workspace (带缓存)

### `save_workspace()`

保存 Workspace (使缓存失效)

### `clear_cache()`

清空缓存

### `get_cache_stats()`

获取缓存统计

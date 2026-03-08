Vector Store - 向量存储封装
基于 SQLiteStorage 的 embedding 功能

## Classes

### `VectorStore`

向量存储 - 语义搜索核心

功能：
- 存储文本和对应的 embedding
- 支持相似度搜索
- 命名空间隔离

**Methods:**
- `add`
- `search`
- `list_namespaces`
- `get_stats`

## Functions

### `get_vector_store()`

获取全局 VectorStore 实例

### `add()`

添加文本到向量存储

### `search()`

语义搜索

### `list_namespaces()`

列出所有命名空间

### `get_stats()`

获取统计信息

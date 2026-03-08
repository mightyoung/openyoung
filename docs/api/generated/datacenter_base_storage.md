BaseStorage - 数据库存储基类
解决代码重复问题，统一错误处理

## Classes

### `BaseStorage`

数据库存储基类 - 解决代码重复问题

**Methods:**
- `close`
- `execute_transaction`
- `transaction`

## Functions

### `get_storage()`

获取存储实例

### `close()`

关闭连接（用于清理）

### `execute_transaction()`

执行事务操作

Args:
    operations: [(query, params), ...] 列表

Returns:
    True 如果成功

### `transaction()`

事务上下文管理器

Usage:
    with storage.transaction():
        storage._execute(query1, params1)
        storage._execute(query2, params2)

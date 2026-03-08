Base Registry - 注册表基类
提供通用的注册表功能

## Classes

### `BaseRegistry`

注册表基类

提供通用功能：
- 目录扫描
- 文件加载
- 使用追踪
- 持久化存储

**Methods:**
- `discover_items`
- `ensure_dir`
- `get_item_path`
- `item_exists`
- `track_usage`
- `get_usage_stats`
- `rate_item`
- `get_ratings`

## Functions

### `discover_items()`

发现目录中的所有项

Args:
    pattern: 匹配模式

Returns:
    List[str]: 项名称列表

### `ensure_dir()`

确保目录存在

### `get_item_path()`

获取项的路径

### `item_exists()`

检查项是否存在

### `track_usage()`

追踪使用

Args:
    item_name: 项名称
    db_name: 数据库文件名

Returns:
    bool: 是否成功

### `get_usage_stats()`

获取使用统计

Args:
    db_name: 数据库文件名
    limit: 返回数量

Returns:
    List[Dict]: 统计列表

### `rate_item()`

评分

Args:
    item_name: 项名称
    rating: 评分 (0-5)

Returns:
    bool: 是否成功

### `get_ratings()`

获取所有评分

Returns:
    Dict[str, float]: 项名称 -> 评分

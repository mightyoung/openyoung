DataLicense - 数据版权管理
轻量级版权追踪
使用 BaseStorage 基类

## Classes

### `DataLicense`

数据许可证

**Methods:**
- `to_dict`

### `Watermark`

数据水印处理器

支持两种水印：
1. 可见水印：嵌入到数据中的可见标识
2. 隐形水印：基于哈希的数字签名，可验证数据来源

**Methods:**
- `generate_watermark`
- `embed_visible_watermark`
- `verify_watermark`
- `remove_watermark`

### `DataLicenseManager`

数据版权管理器

**Methods:**
- `create_license`
- `get_license`
- `list_licenses`
- `check_access`
- `check_permission`

### `AccessLog`

访问日志

**Methods:**
- `log_access`
- `get_logs`

## Functions

### `get_license_manager()`

获取许可证管理器

### `get_access_log()`

获取访问日志

### `add_watermark()`

便捷函数：添加水印

### `verify_watermark()`

便捷函数：验证水印

### `remove_watermark()`

便捷函数：移除水印

### `to_dict()`

### `generate_watermark()`

生成水印标识

Args:
    data: 原始数据
    license_id: 许可证 ID
    owner_id: 所有者 ID
    metadata: 额外元数据

Returns:
    水印字符串

### `embed_visible_watermark()`

嵌入可见水印

Args:
    data: 原始数据（字典或列表）
    license_id: 许可证 ID
    owner_id: 所有者 ID
    metadata: 额外元数据

Returns:
    嵌入水印后的数据

### `verify_watermark()`

验证水印

Args:
    data: 包含水印的数据
    expected_license_id: 期望的许可证 ID
    expected_owner_id: 期望的所有者 ID

Returns:
    验证结果 {
        "valid": bool,
        "license_id": str,
        "owner_id": str,
        "timestamp": str,
        "error": str
    }

### `remove_watermark()`

移除水印

Args:
    data: 包含水印的数据

Returns:
    移除水印后的数据

### `create_license()`

创建许可证

### `get_license()`

获取许可证

### `list_licenses()`

列出许可证

### `check_access()`

检查访问权限

Args:
    license_id: 许可证 ID
    requester_id: 请求者 ID
    team_id: 团队 ID（team 类型许可证需要）

Returns:
    True 如果有权限

### `check_permission()`

检查特定权限

Args:
    license_id: 许可证 ID
    requester_id: 请求者 ID
    required_permission: 需要的权限 (read/write/admin)

Returns:
    True 如果有权限

### `log_access()`

记录访问

### `get_logs()`

获取访问日志

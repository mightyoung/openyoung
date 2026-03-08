Enterprise - 企业级功能
多租户支持、权限控制、审计日志

## Classes

### `Permission`

权限类型

### `IsolationLevel`

隔离级别

### `TenantStatus`

租户状态

### `Tenant`

租户

### `User`

用户

### `AuditLog`

审计日志

### `EnterpriseManager`

企业级管理器

**Methods:**
- `create_tenant`
- `get_tenant`
- `update_tenant`
- `list_tenants`
- `create_user`
- `authenticate`
- `check_permission`
- `log_audit`
- `query_audit_logs`
- `get_audit_stats`

### `IsolationConfig`

隔离配置

**Methods:**
- `get_isolation_path`

### `IsolationManager`

隔离管理器 - 管理多级别数据隔离

**Methods:**
- `create_isolation_dirs`
- `get_isolation_path`
- `is_isolated`
- `save_data`
- `load_data`
- `query_data`
- `delete_data`
- `get_stats`

## Functions

### `get_enterprise_manager()`

获取企业级管理器

### `create_tenant()`

创建租户

### `get_tenant()`

获取租户

### `update_tenant()`

更新租户

### `list_tenants()`

列出租户

### `create_user()`

创建用户

### `authenticate()`

验证用户

### `check_permission()`

检查权限

### `log_audit()`

记录审计日志

### `query_audit_logs()`

查询审计日志

### `get_audit_stats()`

获取审计统计

### `get_isolation_path()`

获取隔离路径

### `create_isolation_dirs()`

创建隔离目录

### `get_isolation_path()`

获取隔离路径

### `is_isolated()`

检查是否启用隔离

### `save_data()`

保存隔离数据

### `load_data()`

加载隔离数据

### `query_data()`

查询隔离数据

### `delete_data()`

删除隔离数据

### `get_stats()`

获取隔离统计

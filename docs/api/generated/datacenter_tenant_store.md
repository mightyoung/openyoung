Tenant DataStore - 租户物理隔离数据存储
每个租户有独立的数据目录和数据库

## Classes

### `TenantDataStore`

租户专属数据存储 - 物理隔离

**Methods:**
- `get_data_dir`
- `export_data`
- `import_data`
- `delete_all_data`

### `TenantManager`

租户管理器

**Methods:**
- `create_tenant`
- `get_tenant`
- `list_tenants`
- `delete_tenant`
- `suspend_tenant`
- `activate_tenant`

## Functions

### `get_tenant_manager()`

获取租户管理器

### `get_tenant_store()`

获取租户数据存储

### `get_data_dir()`

获取租户数据目录

### `export_data()`

导出租户所有数据

### `import_data()`

导入数据

### `delete_all_data()`

删除租户所有数据

### `create_tenant()`

创建租户

### `get_tenant()`

获取租户

### `list_tenants()`

列出租户

### `delete_tenant()`

删除租户

### `suspend_tenant()`

暂停租户

### `activate_tenant()`

激活租户

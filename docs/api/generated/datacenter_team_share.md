TeamShare - 团队数据共享
支持团队内数据共享和权限控制
使用 BaseStorage 基类

## Classes

### `TeamShare`

团队共享记录

### `TeamShareManager`

团队共享管理器

**Methods:**
- `create_team`
- `get_team`
- `list_teams`
- `add_member`
- `remove_member`
- `list_members`
- `share_data`
- `revoke_share`
- `get_shared_data`
- `check_access`

## Functions

### `get_team_share_manager()`

获取团队共享管理器

### `create_team()`

创建团队

### `get_team()`

获取团队信息

### `list_teams()`

列出团队

### `add_member()`

添加团队成员

### `remove_member()`

移除团队成员

### `list_members()`

列出团队成员

### `share_data()`

共享数据给团队

### `revoke_share()`

撤销共享

### `get_shared_data()`

获取团队共享的数据

### `check_access()`

检查用户是否有权访问数据

Args:
    team_id: 团队 ID
    user_id: 用户 ID
    data_id: 数据 ID
    required_permission: 需要的权限 (read/write/admin)

Returns:
    True 如果有权限

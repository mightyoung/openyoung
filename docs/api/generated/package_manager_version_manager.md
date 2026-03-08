Version Manager - Agent 版本管理
支持语义版本控制 (SemVer) 和版本历史追踪

## Classes

### `VersionError`

版本相关错误

### `AgentVersion`

单个版本

### `VersionHistory`

版本历史

**Methods:**
- `get_latest`
- `is_compatible`

### `VersionManager`

版本管理器

**Methods:**
- `get_history`
- `save_history`
- `register_version`
- `get_current_version`
- `list_versions`
- `check_update_available`

## Functions

### `parse_semver()`

解析语义版本号

Args:
    version: 版本字符串 (如 "1.2.3")

Returns:
    (major, minor, patch) 或 None

### `compare_versions()`

比较两个版本

Args:
    v1: 版本1
    v2: 版本2

Returns:
    -1: v1 < v2
     0: v1 == v2
     1: v1 > v2

### `get_version_manager()`

获取版本管理器实例

### `get_latest()`

获取最新版本

Args:
    level: "major", "minor", 或 "patch"

Returns:
    最新的版本对象

### `is_compatible()`

检查版本兼容性

Args:
    version: 当前版本
    target: 目标版本

Returns:
    是否兼容

### `get_history()`

获取版本历史

Args:
    agent_name: Agent 名称

Returns:
    VersionHistory 对象

### `save_history()`

保存版本历史

Args:
    history: VersionHistory 对象

### `register_version()`

注册新版本

Args:
    agent_name: Agent 名称
    version: 版本号
    changelog: 变更日志
    compatible_with: 兼容版本
    breaking_changes: 重大变更列表

Returns:
    新创建的 AgentVersion

### `get_current_version()`

获取当前版本

Args:
    agent_name: Agent 名称

Returns:
    当前版本号或 None

### `list_versions()`

列出版本历史

Args:
    agent_name: Agent 名称
    limit: 返回数量限制

Returns:
    版本列表（按时间倒序）

### `check_update_available()`

检查是否有可用更新

Args:
    agent_name: Agent 名称
    current_version: 当前版本

Returns:
    最新版本号或 None（无可用更新）

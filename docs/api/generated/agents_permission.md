PermissionEvaluator - 权限评估器
对标 OpenCode PermissionNext，实现 ask/allow/deny 三级权限控制

## Classes

### `PermissionEvaluator`

权限评估器 - 对标 OpenCode

实现三级权限控制：
- ALLOW: 无需批准直接执行
- ASK: 提示用户确认
- DENY: 阻止执行

**Methods:**
- `add_rule`
- `remove_rule`
- `set_global`
- `create_allow_all`
- `create_deny_all`
- `create_ask_all`

### `PermissionAskError`

需要用户确认的异常

### `PermissionDeniedError`

权限被拒绝的异常

## Functions

### `add_rule()`

动态添加规则

### `remove_rule()`

移除指定工具的规则

### `set_global()`

设置全局默认权限

### `create_allow_all()`

创建允许所有的权限评估器

### `create_deny_all()`

创建拒绝所有的权限评估器

### `create_ask_all()`

创建询问所有的权限评估器

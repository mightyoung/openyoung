SafetyEval - 安全性评估器
评估输出安全性和有害内容

## Classes

### `SafetyCheck`

安全检查结果

### `SafetyEval`

安全性评估器

功能:
- 有害内容检测
- 敏感信息过滤
- 权限越界检查
- Prompt injection 检测

**Methods:**
- `add_custom_rule`
- `set_blocked`
- `is_blocked`

## Functions

### `create_safety_eval()`

创建 SafetyEval 实例

### `add_custom_rule()`

添加自定义规则

### `set_blocked()`

设置是否阻止所有输出

### `is_blocked()`

检查是否被阻止

TaskDispatcher - 任务调度器
对标 OpenCode task.ts，实现 SubAgent 系统

## Classes

### `Session`

SubAgent 会话

**Methods:**
- `add_message`

### `TaskDispatcher`

任务调度器 - 对标 OpenCode

核心职责：
1. 管理 SubAgent 会话生命周期
2. 构建隔离上下文
3. 调度任务到合适的 SubAgent
4. 聚合结果返回

**Methods:**
- `get_session`
- `list_sessions`

## Functions

### `add_message()`

### `get_session()`

获取会话

### `list_sessions()`

列出所有会话

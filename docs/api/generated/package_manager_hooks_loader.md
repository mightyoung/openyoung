Hooks Configuration Loader
Hooks 配置加载器

## Classes

### `HookTrigger`

Hook 触发时机

### `HookAction`

Hook 动作

### `LearningHook`

自学习 Hook - 集成 Evolver

在任务执行后自动：
1. 收集执行数据
2. 触发 Evolver 进化
3. 创建 Capsule
4. 存储学习模式

**Methods:**
- `on_post_task`

### `HookConfig`

Hook 配置

### `HooksLoader`

Hooks 配置加载器

**Methods:**
- `discover_hooks`
- `load_hooks`
- `get_hooks_by_trigger`
- `register_hook`

## Functions

### `load_hooks_config()`

加载 Hooks 配置 (CLI 入口)

### `on_post_task()`

Post-task 自学习钩子

### `discover_hooks()`

发现所有 Hooks 包

### `load_hooks()`

加载 Hooks 配置

### `get_hooks_by_trigger()`

获取指定触发时机的 Hooks

### `register_hook()`

注册 Hook

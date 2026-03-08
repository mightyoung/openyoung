TokenTracker - Token 使用追踪
记录 LLM 调用级别的 token 使用情况
使用 BaseStorage 基类

## Classes

### `TokenRecord`

Token 使用记录

### `TokenTracker`

Token 使用追踪器

**Methods:**
- `record`
- `get_by_run`
- `get_by_step`
- `get_summary`
- `get_by_model`
- `check_budget`
- `get_trend`
- `delete_by_run`

## Functions

### `get_token_tracker()`

获取 TokenTracker 实例（便捷函数）

### `record()`

记录一次 LLM 调用的 token 使用

Args:
    run_id: Run ID
    model: 模型名
    provider: 提供商 (openai/anthropic/deepseek)
    input_tokens: 输入 token 数
    output_tokens: 输出 token 数
    step_id: Step ID (可选)
    reasoning_tokens: 推理 token 数
    latency_ms: 延迟（毫秒）
    metadata: 额外元数据

Returns:
    token_id

### `get_by_run()`

获取某个 Run 的所有 token 记录

Args:
    run_id: Run ID

Returns:
    token 记录列表

### `get_by_step()`

获取某个 Step 的 token 记录

Args:
    step_id: Step ID

Returns:
    token 记录列表

### `get_summary()`

获取 token 使用摘要

Args:
    run_id: Run ID (可选，不提供则返回全局)

Returns:
    摘要字典

### `get_by_model()`

按模型统计 token 使用

Args:
    run_id: Run ID (可选)

Returns:
    按模型的统计列表

### `check_budget()`

检查是否超出预算

Args:
    run_id: Run ID (可选)
    budget_usd: 预算（美元）
    budget_tokens: 预算（token 数）

Returns:
    预算检查结果

### `get_trend()`

获取每日 token 使用趋势

Args:
    days: 天数

Returns:
    每日统计列表

### `delete_by_run()`

删除某个 Run 的所有 token 记录

Args:
    run_id: Run ID

Returns:
    删除的记录数

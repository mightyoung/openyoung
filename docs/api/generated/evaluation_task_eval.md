TaskCompletionEval - 任务完成评估器
评估 Agent 任务完成能力

## Classes

### `TaskTrace`

任务执行轨迹

### `TaskMetrics`

任务指标

### `TaskCompletionEval`

任务完成评估器

功能:
- 任务成功率评估
- 步骤效率评估
- 执行时间评估
- 错误恢复评估
- 一致性评估 (多次运行)

**Methods:**
- `add_trace`
- `get_traces`
- `clear_traces`

## Functions

### `create_task_eval()`

创建 TaskCompletionEval 实例

### `add_trace()`

添加任务轨迹

### `get_traces()`

获取所有轨迹

### `clear_traces()`

清空轨迹

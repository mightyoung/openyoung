DataIntegration - 数据追踪集成
将 RunTracker、StepRecorder 集成到 Agent 执行流程

## Classes

### `DataTrackerMixin`

数据追踪 Mixin - 混入 Agent 类实现自动追踪

**Methods:**
- `enable_tracking`
- `start_run_tracking`
- `complete_run_tracking`
- `fail_run_tracking`
- `start_step_tracking`
- `complete_step_tracking`
- `fail_step_tracking`

### `TrackingContext`

追踪上下文管理器

## Functions

### `track_step()`

步骤追踪上下文管理器（同步版本）

### `enable_tracking()`

启用数据追踪

### `start_run_tracking()`

开始运行追踪

### `complete_run_tracking()`

完成运行追踪

### `fail_run_tracking()`

标记运行失败

### `start_step_tracking()`

开始步骤追踪

### `complete_step_tracking()`

完成步骤追踪

### `fail_step_tracking()`

标记步骤失败

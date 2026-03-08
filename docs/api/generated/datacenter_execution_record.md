统一执行记录模型 - R2-3 DataCenter 存储统一

提供 ExecutionRecord 作为统一的数据模型，替代分散的 TraceRecord, RunRecord, StepRecord

## Classes

### `ExecutionStatus`

执行状态常量

### `ExecutionRecord`

统一的执行记录模型

整合 TraceRecord, RunRecord, StepRecord 为单一模型
支持层级追溯: execution → run → step

**Methods:**
- `to_dict`
- `from_dict`
- `mark_running`
- `mark_success`
- `mark_failed`
- `add_step`

### `RecordAdapter`

记录适配器 - 兼容现有模型

**Methods:**
- `from_trace`
- `from_run`
- `from_step`

## Functions

### `to_dict()`

转换为字典

### `from_dict()`

从字典创建

### `mark_running()`

标记为运行中

### `mark_success()`

标记为成功

### `mark_failed()`

标记为失败

### `add_step()`

添加步骤记录

### `from_trace()`

从 TraceRecord 转换

### `from_run()`

从 RunRecord 转换

### `from_step()`

从 StepRecord 转换

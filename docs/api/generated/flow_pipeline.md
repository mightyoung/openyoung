Pipeline - 声明式任务管道
对标 LangGraph StateGraph，实现 DAG 编排

## Classes

### `StageStatus`

Stage 执行状态

### `Stage`

管道阶段

### `PipelineContext`

管道执行上下文

**Methods:**
- `get_result`
- `set_result`
- `get_error`
- `set_error`
- `is_ready`

### `Pipeline`

管道抽象类

使用方式：
1. 继承 Pipeline
2. 定义 stages()
3. 实现 execute_stage()

**Methods:**
- `add_stage`
- `get_stages`
- `get_stage`
- `topological_sort`

### `PipelineExecutor`

管道执行器 - 执行多个 Pipeline

**Methods:**
- `register`

### `ExamplePipeline`

示例管道：代码开发流程

### `SimplePipeline`

## Functions

### `create_pipeline()`

创建管道的便捷函数

Args:
    name: 管道名称
    stages: Stage 配置列表
        [
            {"name": "stage1", "depends_on": []},
            {"name": "stage2", "depends_on": ["stage1"]}
        ]
    executor: 自定义执行函数

Returns:
    Pipeline 实例

### `get_result()`

获取 Stage 执行结果

### `set_result()`

设置 Stage 执行结果

### `get_error()`

获取 Stage 错误

### `set_error()`

设置 Stage 错误

### `is_ready()`

检查 Stage 是否准备好执行（所有依赖已完成）

### `add_stage()`

添加 Stage

### `get_stages()`

获取所有 Stages

### `get_stage()`

获取指定 Stage

### `topological_sort()`

拓扑排序（用于确定执行顺序）

### `register()`

注册管道

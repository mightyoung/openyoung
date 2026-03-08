EvalSubAgent - 评估子代理
负责从 Hub 加载包、并行执行评估器、聚合结果

## Classes

### `EvalResult`

单项评估结果

**Methods:**
- `to_dict`

### `EvaluationReport`

评估报告

**Methods:**
- `to_dict`

### `EvalSubAgent`

评估子代理 - 负责执行评估

功能:
- 从 Hub 搜索评估包
- 加载评估器
- 并行/串行执行评估
- 聚合评估结果

## Functions

### `create_eval_subagent()`

创建 EvalSubAgent 实例的便捷函数

### `to_dict()`

### `to_dict()`

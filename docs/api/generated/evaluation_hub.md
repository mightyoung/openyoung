EvaluationHub - 评估中心
整合所有评估器

## Classes

### `EvaluationResult`

评估结果

### `EvaluationHub`

评估中心 - 管理和执行评估

整合 CodeEval, TaskCompletionEval, LLMJudgeEval, SafetyEval
提供统一的评估接口

**Methods:**
- `register_metric`
- `register_package`
- `register_evaluator`
- `list_metrics`
- `list_packages`
- `list_evaluators`
- `optimize_agent_config`
- `get_latest_result`
- `save_history`
- `get_history`
- `get_trend`
- `get_results`
- `get_results_by_metric`
- `clear_results`
- `save_results`
- `load_results`
- `clear_results`
- `get_trend`
- `register_eval_package`
- `search_packages`
- `load_evaluators`
- `search_eval_packages`
- `get_eval_package`
- `list_all_eval_packages`

## Functions

### `create_evaluation_hub()`

创建 EvaluationHub 实例

### `register_metric()`

注册评估指标

### `register_package()`

注册评估包

### `register_evaluator()`

注册自定义评估器

### `list_metrics()`

列出所有指标

### `list_packages()`

列出所有评估包

### `list_evaluators()`

列出所有评估器

### `optimize_agent_config()`

根据评估结果优化 agent 配置

Args:
    agent_name: Agent 名称
    eval_result: 评估结果

Returns:
    配置更新字典，包含 model, temperature, max_tokens 等

### `get_latest_result()`

获取最新的评估结果

### `save_history()`

保存评估历史到 SQLite

### `get_history()`

获取评估历史

### `get_trend()`

获取评估趋势

### `get_results()`

获取评估结果

### `get_results_by_metric()`

获取指定指标的结果

### `clear_results()`

清空评估结果

### `save_results()`

保存评估结果到JSON文件

### `load_results()`

从JSON文件加载评估结果

### `clear_results()`

清空评估结果

### `get_trend()`

获取评估趋势数据

Args:
    limit: 返回最近 N 条记录

Returns:
    趋势数据字典

### `register_eval_package()`

注册评估包到索引

### `search_packages()`

搜索评估包

Args:
    feature_codes: 特征码列表
    dimension: 评估维度
    level: 评估层级

Returns:
    匹配的评估包列表（包括内置包字典）

### `load_evaluators()`

从包中加载评估器

Args:
    package: 评估包

Returns:
    评估器实例列表

### `search_eval_packages()`

搜索评估包

### `get_eval_package()`

获取评估包

### `list_all_eval_packages()`

列出所有评估包

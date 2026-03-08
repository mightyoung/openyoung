YoungAgent - Main Agent Class with full system integration

## Classes

### `YoungAgent`

**Methods:**
- `switch_flow_skill`
- `get_harness_stats`
- `get_datacenter_traces`
- `get_evaluation_results`
- `get_evolver_genes`
- `get_evolver_capsules`
- `get_all_stats`
- `get_evaluation_trend`

## Functions

### `calculate_weighted_score()`

根据任务类型计算加权评分

Args:
    task_type: 任务类型 (coding/general/conversation/research/...)
    base_score: LLMJudge 基础评分 (0-1)
    completion_rate: 任务完成度 (0-1)
    efficiency: 执行效率 (0-1)

Returns:
    加权后的评分 (0-1)

### `check_threshold_violations()`

检查是否低于阈值

Args:
    judge_result: LLMJudge 评估结果

Returns:
    违反阈值的维度列表

### `validate_file_creation()`

验证文件是否真实创建

从任务描述中提取可能的文件路径，然后检查这些路径是否存在。
如果任务描述中提到保存到文件，但文件未创建，则返回失败。

Args:
    task_description: 任务描述
    agent_result: Agent 的执行结果

Returns:
    验证结果: {"verified": bool, "files_found": list, "files_expected": list, "message": str}

### `switch_flow_skill()`

运行时切换 FlowSkill

### `get_harness_stats()`

### `get_datacenter_traces()`

### `get_evaluation_results()`

### `get_evolver_genes()`

### `get_evolver_capsules()`

### `get_all_stats()`

### `get_evaluation_trend()`

获取评估趋势数据

Args:
    limit: 返回最近 N 条记录

Returns:
    趋势数据字典

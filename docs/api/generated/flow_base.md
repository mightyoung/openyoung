FlowSkill - 工作流编排基类
对标 OpenCode，实现 Flow Skill 机制

## Classes

### `FlowSkill`

Flow Skill - 控制 Agent 工作流编排

核心接口：
- pre_process: 前置处理（用户输入到达 Agent 前）
- post_process: 后置处理（Agent 输出返回前）
- should_delegate: 判断是否需要委托给 SubAgent
- get_subagent_type: 获取合适的 SubAgent 类型
- get_pipeline: 返回执行管道（可选）
- get_subtasks: 分解为子任务（可选）

**Methods:**
- `name`
- `description`
- `trigger_patterns`
- `parallel_stages`

## Functions

### `name()`

Flow Skill 名称

### `description()`

Flow Skill 描述

### `trigger_patterns()`

触发模式

### `parallel_stages()`

可并行执行的 Stage 名称列表

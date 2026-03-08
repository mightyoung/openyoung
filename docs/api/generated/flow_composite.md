CompositeFlowSkill - 组合多个 FlowSkill
支持链式组合、并行组合、条件组合

## Classes

### `CompositionType`

组合类型

### `CompositeConfig`

组合配置

### `CompositeFlowSkill`

组合 FlowSkill

将多个 FlowSkill 组合在一起，支持：
- 链式组合：顺序执行多个 Skill
- 并行组合：同时执行多个 Skill
- 条件组合：根据条件选择 Skill

**Methods:**
- `name`
- `description`
- `trigger_patterns`

### `ChainFlowSkill`

链式组合 Skill

多个 Skill 依次执行，前一个的输出作为后一个的输入

### `ParallelFlowSkill`

并行组合 Skill

多个 Skill 同时执行，结果合并

**Methods:**
- `parallel_stages`

### `ConditionalFlowSkill`

条件组合 Skill

根据条件选择执行哪个 Skill

## Functions

### `compose_skills()`

组合多个 Skill 为链式 Skill

### `compose_parallel()`

组合多个 Skill 为并行 Skill

### `compose_conditional()`

组合多个 Skill 为条件 Skill

### `name()`

### `description()`

### `trigger_patterns()`

合并所有 Skill 的触发模式

### `parallel_stages()`

所有 Skill 都可并行

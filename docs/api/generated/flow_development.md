DevelopmentFlow - 集成开发工作流
基于 integrated-dev-workflow 构建

## Classes

### `DevelopmentFlow`

DevelopmentFlow - 完整的开发工作流编排

基于 integrated-dev-workflow，实现:
- Phase 1: Requirements & Design
- Phase 2: Technical Planning
- Phase 3: Implementation (TDD)
- Phase 4: Testing & Review
- Phase 5: Completion

智能路由:
- URL 检测 → 自动使用 summarize 技能
- "如何做" / "how to" → 自动使用 find-skills 技能
- 其他 → 正常开发流程

文件跟踪:
- task_plan.md - 任务计划和进度
- findings.md - 研究和决策
- progress.md - 会话日志和测试结果

**Methods:**
- `name`
- `description`
- `trigger_patterns`

## Functions

### `create_development_flow()`

创建 DevelopmentFlow 实例

### `name()`

### `description()`

### `trigger_patterns()`

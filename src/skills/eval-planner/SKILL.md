# Eval Planner Skill (DEPRECATED)

> **DEPRECATED** — 评估功能已迁移到 **Harness 系统** (`src/hub/evaluate/`)

评估规划功能已整合到 Harness 评估框架，使用 `BenchmarkTask` + `Grader` 模式。
请使用新系统，参考 `src/hub/evaluate/` 目录。

## Migration Guide

### Old System (DEPRECATED)
```python
from src.evaluation.planner import EvalPlanner
planner = EvalPlanner()
eval_plan = await planner.generate_plan(task_description)
```

### New System (Harness)
```python
from src.hub.evaluate import BenchmarkTask, EvalRunner, RunnerConfig

runner = EvalRunner(RunnerConfig())
task = BenchmarkTask(...)
result = await runner.run(task)
```

## Legacy Reference

This skill previously provided:
- Task type analysis
- Success criteria generation
- Validation method generation
- Metrics definition

All functionality is now handled by the Harness system at `src/hub/evaluate/`:
- `benchmark.py` — BenchmarkTask definition
- `evaluator.py` — Grader patterns
- `runner.py` — EvalRunner execution
- `metrics.py` — Metric definitions

## CLI Commands

```bash
# Old (deprecated)
openyoung eval run "task"

# New
openyoung harness run --task <task_name>
openyoung webui  # then navigate to Dashboard
```

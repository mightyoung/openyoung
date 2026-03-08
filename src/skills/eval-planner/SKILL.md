# Eval Planner Skill

## Overview

This skill generates evaluation plans for tasks before execution. It analyzes task types, creates success criteria, validation methods, metrics, and searches for best practices from GitHub and the internet.

## When to Use

Use this skill when:
- User asks to generate an evaluation plan
- User wants to evaluate task quality before/after execution
- User mentions success criteria, validation methods, or metrics
- User wants to assess task completion rate
- User wants to search best practices for task evaluation

## Workflow

### Step 1: Analyze Task Type

Analyze the task description to identify the task type. Common types include:

| Task Type | Keywords |
|-----------|----------|
| web_scraping | 爬, 抓取, 采集, scrape, crawl, 热榜 |
| coding | 写, 实现, 创建, 开发, write, implement |
| analysis | 分析, 解析, 评估, analyze, analysis |
| research | 研究, 调查, 搜索, research, investigate |
| refactor | 重构, 优化, 改进, refactor, optimize |
| debug | 调试, 修复, 错误, debug, fix, bug |

### Step 2: Generate Success Criteria

Based on task type, generate relevant success criteria:

```
web_scraping:
  - 成功获取指定数量的数据
  - 数据包含所需字段
  - 数据保存到指定位置
  - 输出格式正确

coding:
  - 代码无语法错误
  - 代码功能正确
  - 包含必要的测试
  - 代码符合规范

analysis:
  - 分析结果完整
  - 包含数据支持
  - 结论清晰
  - 输出格式正确
```

### Step 3: Generate Validation Methods

Create specific validation steps:

```
web_scraping:
  - 检查输出文件是否存在
  - 验证数据格式(JSON/CSV)
  - 验证数据条目数量
  - 验证必需字段存在
  - 检查数据是否为空

coding:
  - 运行代码无错误
  - 输出结果正确
  - 通过单元测试
  - 符合编码规范
```

### Step 4: Generate Metrics

Define evaluation metrics:

```
web_scraping:
  - completeness - 数据完整性
  - accuracy - 数据准确性
  - freshness - 数据时效性

coding:
  - correctness - 代码正确性
  - quality - 代码质量
  - testability - 可测试性
```

### Step 5: Parse Expected Outputs

Extract from task description:
- **format**: json, csv, markdown, etc.
- **location**: output path
- **count**: number of items
- **fields**: required fields

### Step 6: Search Best Practices

Search for evaluation best practices:

1. **GitHub sources**:
   - anthropics/claude-code evals
   - openai/evals
   - evals/evals
   - langchain-ai/evals

2. **Web search** (based on task type):
   - "web scraping evaluation"
   - "code quality evaluation"
   - "data analysis evaluation"

### Step 7: Generate Evaluation Plan

Create the final evaluation plan structure:

```python
@dataclass
class EvalPlan:
    task_description: str
    task_type: str
    success_criteria: List[str]
    validation_methods: List[str]
    metrics: List[str]
    expected_outputs: Dict[str, Any]
    evaluation_steps: List[str]
    sources: List[str]
```

## Code Implementation

### Using EvalPlanner Class

```python
from src.evaluation.planner import EvalPlanner

# Create planner
planner = EvalPlanner()

# Generate evaluation plan
eval_plan = await planner.generate_plan(task_description)

# Access plan details
print(f"Task type: {eval_plan.task_type}")
print(f"Success criteria: {eval_plan.success_criteria}")
print(f"Validation methods: {eval_plan.validation_methods}")
print(f"Metrics: {eval_plan.metrics}")
print(f"Expected outputs: {eval_plan.expected_outputs}")
print(f"Sources: {eval_plan.sources}")
```

### Enhanced Evaluation

After task execution, use the evaluation plan to score results:

```python
def evaluate_with_plan(result: str, eval_plan) -> float:
    """Evaluate task result based on evaluation plan"""
    completion_rate = 0.0

    if eval_plan.success_criteria:
        completed = 0
        result_lower = result.lower()

        for criterion in eval_plan.success_criteria:
            matched = False

            # Extract keywords from criterion
            keywords = re.findall(r'[\u4e00-\u9fa5a-zA-Z0-9]{2,}', criterion)

            # Check if any keyword matches
            for kw in keywords:
                if len(kw) >= 2 and kw.lower() in result_lower:
                    matched = True
                    break

            # Task-specific matching
            if eval_plan.task_type == "web_scraping":
                # Check count
                nums = re.findall(r'\d+', criterion)
                if nums and any(n in result for n in nums):
                    matched = True
                # Check save location
                if "保存" in criterion or "位置" in criterion:
                    if "保存" in result or "output" in result_lower:
                        matched = True
                # Check format
                if "格式" in criterion or "JSON" in criterion.upper():
                    if "json" in result_lower or "csv" in result_lower:
                        matched = True

            if matched:
                completed += 1

        completion_rate = completed / len(eval_plan.success_criteria)

    return completion_rate
```

## Example

### Input
```
"从小红书上爬取热榜前十的帖子信息与评论"
```

### Output
```json
{
  "task_type": "web_scraping",
  "success_criteria": [
    "成功获取热榜前10帖子",
    "每条帖子包含: 标题、作者、点赞数、评论数",
    "数据保存到指定目录",
    "输出格式为JSON"
  ],
  "validation_methods": [
    "检查输出文件是否存在",
    "验证JSON格式正确",
    "验证数据条目数量=10",
    "验证每个字段非空"
  ],
  "metrics": [
    "completeness - 数据完整性",
    "accuracy - 数据准确性",
    "format - 格式正确性"
  ],
  "expected_outputs": {
    "format": "json",
    "count": 10,
    "fields": ["rank", "title", "author", "likes", "comments"]
  },
  "sources": [
    "GitHub: anthropics/claude-code evals",
    "GitHub: openai/evals",
    "Web: web scraping evaluation best practices"
  ]
}
```

## Integration

This skill integrates with:
- `src/evaluation/planner.py` - Core EvalPlanner class
- `src/evaluation/task_eval.py` - TaskCompletionEval
- `src/evaluation/hub.py` - EvaluationHub

Use in agent workflow:
1. Before task execution: generate evaluation plan
2. After task execution: evaluate result using the plan
3. Report quality score based on completion rate

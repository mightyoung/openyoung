LLMJudgeEval - LLM 评判评估器
使用 LLM 进行质量评估

## Classes

### `JudgeScore`

评判分数

### `LLMJudgeEval`

LLM 评判评估器

功能:
- 多维度评分 (正确性/效率/安全/体验)
- Pairwise 对比评估
- Position bias 缓解
- 评分标准 (Rubric)

**Methods:**
- `set_rubric`
- `get_rubric`

## Functions

### `create_llm_judge()`

创建 LLMJudgeEval 实例

### `set_rubric()`

设置自定义评分标准

### `get_rubric()`

获取当前评分标准

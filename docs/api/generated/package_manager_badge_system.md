Badge System - 质量徽章系统
为 Agent 授予各种质量徽章

## Classes

### `BadgeType`

徽章类型

### `Badge`

徽章

### `BadgeSystem`

徽章系统

**Methods:**
- `calculate_trending_score`
- `format_badges`

## Functions

### `calculate_trending_score()`

计算趋势分数

公式：
- velocity_score: 下载增长速度 (0-10)
- rating_score: 评分 (0-5)
- freshness_score: 新鲜度 (0-1)

### `format_badges()`

格式化徽章为字符串

# 评估系统问题分析

> 分析时间: 2026-03-10

---

## 一、问题列表

### 1.1 traces.json 数据不全

**问题**: 仅记录一条 default agent 执行记录

**原因分析**:
- traces.json 仅记录最后一次执行
- 缺少历史执行记录
- 断点未正确保存

**当前状态**:
```json
[{
  "session_id": "967ee799-...",
  "agent_name": "default",
  "status": "success"
}]
```

---

### 1.2 评估逻辑问题

**问题**: 对 "Hello, say hi" 这种简单问候也进行完整评估

**问题根源**:
- 缺少任务复杂度判断
- 所有任务都触发完整评估流程
- 没有跳过简单任务的逻辑

**不应该评估的情况**:
- 问候语 ("Hello", "Hi")
- 简单查询 ("What's 1+1?")
- 无意义输入

---

### 1.3 数据未存入 SQLite

**现状**:
- `data.db` 有 `traces` 和 `evaluations` 表
- 但数据可能未正确写入
- `traces.json` 和 `evaluations.json` 有数据

**需要验证**:
```sql
SELECT COUNT(*) FROM traces;  -- 应该 > 0
SELECT COUNT(*) FROM evaluations;  -- 应该 > 0
```

---

### 1.4 评估失败时未触发自循环

**问题**: 低分评估结果没有触发重试机制

**期望流程**:
```
Agent执行 → 评估 → 低分 → Ralph循环 → 改进 → 重执行 → 再次评估
```

**当前缺失**:
- 评估结果没有反馈给执行器
- 没有自动重试逻辑
- Rust端没有接收评估结果的接口

---

## 二、需要深入探讨的问题

### 2.1 评估生成逻辑

**问题**: 评估是如何触发的？

**可能的触发点**:
1. CLI 命令 `openyoung run` 时自动触发
2. Agent 执行完成后触发
3. 手动调用 `openyoung eval` 触发

**需要确认**:
- 评估阈值是多少？ (如 score < 0.6 为失败)
- 哪些维度被评估？
- 评估结果如何影响后续执行？

### 2.2 数据流架构

**问题**: 数据如何在组件间流动？

```
User Input → CLI → Agent → Execution → Evaluation → Storage
                              ↓
                         ContextCollector → traces.json
                              ↓
                         Evaluator → evaluations.json
```

**需要确认**:
- ContextCollector 收集的数据是否完整？
- 评估结果是否写入了 SQLite？
- Rust 端如何接收数据？

---

## 三、改进建议

### 3.1 任务复杂度过滤

```python
# 建议：简单任务不评估
SKIP_EVAL_PATTERNS = [
    r"^(hello|hi|hey|howdy)",
    r"^say\s+\w+$",
    r"^(what|who|where)\s+is\s+\d+[\s+\d+]*\?$",
]

def should_evaluate(task: str) -> bool:
    """判断任务是否需要评估"""
    for pattern in SKIP_EVAL_PATTERNS:
        if re.match(pattern, task.lower()):
            return False
    return True
```

### 3.2 完善数据持久化

```python
# 确保评估结果写入 SQLite
def save_evaluation_to_db(evaluation: dict):
    conn = sqlite3.connect('.young/data.db')
    conn.execute("""
        INSERT INTO evaluations (session_id, metric, score, details, evaluator)
        VALUES (?, ?, ?, ?, ?)
    """, (
        evaluation['session_id'],
        evaluation['metric'],
        evaluation['score'],
        json.dumps(evaluation['details']),
        evaluation.get('evaluator', 'default')
    ))
    conn.commit()
```

### 3.3 Ralph 循环集成

```python
# 评估失败时触发重试
def handle_low_score(score: float, evaluation: dict):
    if score < THRESHOLD:
        # 触发 Ralph 循环
        trigger_ralph_loop(
            original_task=evaluation['task'],
            feedback=evaluation['details'],
            iteration=evaluation.get('iteration', 0) + 1
        )
```

---

## 四、下一步行动

1. **确认评估触发点** - 查找代码中评估触发的位置
2. **验证数据持久化** - 检查 SQLite 是否真的有数据
3. **设计复杂度过滤** - 区分简单任务和复杂任务
4. **实现自循环** - Ralph 循环与评估结果集成
5. **设计 Rust 接口** - 让评估结果能返回给 Rust

---

## 五、需要讨论的问题

1. **评估应该什么时候触发？**
   - 每次执行后？
   - 仅在用户请求时？
   - 仅在复杂任务时？

2. **评估维度有哪些？**
   - 正确性 (correctness)
   - 效率 (efficiency)
   - 安全性 (safety)
   - 其他？

3. **Ralph 循环应该如何与评估集成？**
   - 评估失败 → 自动重试？
   - 评估成功 → 继续下一步？
   - 评估中等 → 可以重试？

4. **数据存储策略？**
   - 每次执行都存？
   - 仅存评估结果？
   - 存完整上下文？

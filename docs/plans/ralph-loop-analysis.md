# OpenYoung Agent 架构改进研究

> 基于 oh-my-openagent (Ralph Loop) 的分析

---

## 核心发现

### 1. Ralph Loop 设计

**概念**: 自我引用的循环，"不完成不停止"

```
用户输入 → Sisyphus (主调度)
    ↓
选择 Agent 类别 (visual/deep/quick/ultrabrain)
    ↓
并行启动 5+ 专家 Agent
    ↓
结果聚合 ← Todo Enforcer (拉回空闲 Agent)
    ↓
循环直到 100% 完成
```

### 2. Agent 定义对比

| oh-my-openagent | 角色 | OpenYoung 当前 | 建议 |
|-----------------|------|----------------|------|
| Sisyphus | 主调度 | YoungAgent | ✅ 已类似 |
| Hephaestus | 深度执行 | SubAgent (deep) | 可增强 |
| Prometheus | 战略规划 | EvaluationCoordinator | ✅ 已类似 |
| Oracle | 架构/调试 | 可新增 | 专家 Agent |
| Librarian | 文档/搜索 | SkillLoader | ✅ 已类似 |
| Explore | 快速搜索 | 可增强 | 增强搜索 |

---

## Best Minds 分析

### Andrej Karpathy 视角

> "Don't think of LLMs as entities but as simulators."

Karpathy 会指出：

1. **Agent 是模拟器，不是工具**
   - Ralph Loop 的核心是"持续模拟开发团队直到完成"
   - 不是执行单个任务，而是模拟完整的开发过程

2. **Agent 分类而非模型选择**
   - "picks a category rather than a model"
   - 按能力分类：visual-engineering, deep, quick, ultrabrain
   - 好处：解耦 + 可替换 + 自适应

3. **背景并行是关键**
   - "5+ specialists in parallel"
   - 主 Agent spawn 后台任务，不等待

### John Carmack 视角

> "The right thing to do is to keep iterating."

Carmack 会强调：

1. **快速迭代**
   - Ralph Loop 快速循环直到完成
   - 每个循环都是学习机会

2. **端到端**
   - Hephaestus 是 "end-to-end" worker
   - 不需要人工干预

---

## 改进建议

### 1. Ralph Loop 机制

```python
# 建议实现
class RalphLoop:
    """自主循环直到完成"""

    def __init__(self, max_iterations=10):
        self.max_iterations = max_iterations
        self.iteration_count = 0

    async def run_until_complete(self, task, context):
        while not task.is_complete and self.iteration_count < self.max_iterations:
            # 1. 规划当前迭代
            plan = await self.plan_iteration(task, context)

            # 2. 并行执行子任务
            results = await self.execute_parallel(plan)

            # 3. 评估结果
            evaluation = await self.evaluate(results)

            # 4. 如果不完整，继续
            if not evaluation.is_complete:
                context = self.update_context(context, results)
                self.iteration_count += 1
            else:
                break

        return self.aggregate_results(context)
```

### 2. Agent 分类系统

```python
# 建议的 Agent 分类
AGENT_CATEGORIES = {
    "quick": {
        "description": "快速简单任务",
        "timeout": 60,
        "model": "haiku",
    },
    "visual": {
        "description": "界面/前端相关",
        "timeout": 300,
        "model": "sonnet",
    },
    "deep": {
        "description": "复杂深度任务",
        "timeout": 600,
        "model": "opus",
    },
    "ultrabrain": {
        "description": "需要深度思考",
        "timeout": 900,
        "model": "opus",
    },
}
```

### 3. Todo Enforcer

```python
class TodoEnforcer:
    """拉回空闲 Agent 确保任务完成"""

    def __init__(self):
        self.idle_agents = []
        self.active_tasks = {}

    def register_idle(self, agent_id):
        """注册空闲 Agent"""
        self.idle_agents.append(agent_id)

    def pull_back(self, task_id):
        """拉回空闲 Agent 完成任务"""
        if self.idle_agents:
            agent_id = self.idle_agents.pop()
            self.assign_task(agent_id, task_id)
```

---

## 实施优先级

| 优先级 | 改进项 | 预期收益 | 难度 |
|--------|--------|----------|------|
| P0 | Agent 分类系统 | 解耦 + 自适应 | 中 |
| P1 | Ralph Loop | 自主完成 | 高 |
| P2 | Todo Enforcer | 防止挂起 | 中 |
| P3 | 新增 Oracle Agent | 架构支持 | 低 |

---

## 参考资料

- oh-my-openagent: https://github.com/code-yeongyu/oh-my-openagent
- Andrej Karpathy: "LLMs as simulators"
- John Carmack: 迭代开发理念

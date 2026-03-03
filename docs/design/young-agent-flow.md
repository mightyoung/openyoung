# YoungAgent Flow Skill 设计

> 版本: 1.0.0
> 更新日期: 2026-03-01

---

## 1. Flow Skill 概述

Flow Skill 是控制 Agent 工作流编排的机制，允许通过声明式配置定义复杂的工作流程。

---

## 2. FlowSkill 接口

```python
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

class FlowSkill(ABC):
    """Flow Skill - 控制 Agent 工作流编排"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Flow Skill 名称"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Flow Skill 描述"""
        pass
    
    @property
    def trigger_patterns(self) -> list[str]:
        """触发模式"""
        return []
    
    @abstractmethod
    async def pre_process(self, user_input: str, context: dict) -> str:
        """前置处理 - 用户输入到达 Agent 前调用"""
        pass
    
    @abstractmethod
    async def post_process(self, agent_output: str, context: dict) -> str:
        """后置处理 - Agent 输出返回前调用"""
        pass
    
    async def should_delegate(self, task: str, context: dict) -> bool:
        """判断是否需要委托给 SubAgent"""
        pass
    
    async def get_subagent_type(self, task: str) -> Optional[str]:
        """获取合适的 SubAgent 类型"""
        pass
```

---

## 3. 内置 Flow Skills

| Flow Skill | 用途 |
|------------|------|
| **SequentialFlow** | 串行执行多个步骤 |
| **ParallelFlow** | 并行执行多个子任务 |
| **ConditionalFlow** | 条件分支执行 |
| **LoopFlow** | 循环执行直到满足条件 |

### 3.1 SequentialFlow

```python
class SequentialFlow(FlowSkill):
    """串行执行 Flow"""
    
    name = "sequential"
    description = "串行执行多个步骤"
    
    def __init__(self, steps: list[dict]):
        self.steps = steps
    
    async def pre_process(self, user_input: str, context: dict) -> str:
        # 分解任务为步骤
        steps = self._decompose(user_input)
        context["_flow_steps"] = steps
        context["_current_step"] = 0
        return user_input
    
    async def post_process(self, agent_output: str, context: dict) -> str:
        # 检查是否完成所有步骤
        current = context.get("_current_step", 0)
        total = len(context.get("_flow_steps", []))
        
        if current < total - 1:
            # 还有步骤，继续
            context["_current_step"] = current + 1
            return f"步骤 {current + 1}/{total} 完成，继续执行..."
        
        return agent_output
```

### 3.2 ParallelFlow

```python
class ParallelFlow(FlowSkill):
    """并行执行 Flow"""
    
    name = "parallel"
    description = "并行执行多个子任务"
    
    def __init__(self, max_concurrent: int = 3):
        self.max_concurrent = max_concurrent
    
    async def pre_process(self, user_input: str, context: dict) -> str:
        # 识别可并行的子任务
        subtasks = self._identify_parallel_tasks(user_input)
        context["_parallel_tasks"] = subtasks
        return user_input
    
    async def post_process(self, agent_output: str, context: dict) -> str:
        # 聚合并行结果
        results = context.get("_parallel_results", [])
        return self._aggregate_results(results)
```

### 3.3 ConditionalFlow

```python
class ConditionalFlow(FlowSkill):
    """条件分支 Flow"""
    
    name = "conditional"
    description = "条件分支执行"
    
    def __init__(self, conditions: dict[Callable, str]):
        # conditions: {condition_fn: branch_name}
        self.conditions = conditions
    
    async def pre_process(self, user_input: str, context: dict) -> str:
        # 评估条件
        for condition, branch in self.conditions.items():
            if await condition(user_input, context):
                context["_current_branch"] = branch
                break
        return user_input
```

### 3.4 LoopFlow

```python
class LoopFlow(FlowSkill):
    """循环执行 Flow"""
    
    name = "loop"
    description = "循环执行直到满足条件"
    
    def __init__(self, max_iterations: int = 5):
        self.max_iterations = max_iterations
    
    async def pre_process(self, user_input: str, context: dict) -> str:
        context["_loop_iteration"] = 0
        return user_input
    
    async def post_process(self, agent_output: str, context: dict) -> str:
        iteration = context.get("_loop_iteration", 0)
        
        # 检查是否满足退出条件
        if self._should_continue(agent_output, context):
            if iteration < self.max_iterations:
                context["_loop_iteration"] = iteration + 1
                return f"循环迭代 {iteration + 1}/{self.max_iterations}，继续..."
        
        return agent_output
```

---

## 4. Flow Skill 变量配置

Flow Skill 通过占位符 `${flow_skills}` 动态加载：

```yaml
# young.yaml - Agent 配置
agent:
  name: "my-agent"
  prompt:
    # Flow Skill 配置
    flow_skills:
      enabled: true
      skills:
        - name: "code-review"
          description: "代码审查流程"
        - name: "test-generator"
          description: "测试生成流程"
```

#### 配置项说明

| 配置项 | 类型 | 说明 |
|--------|------|------|
| `flow_skills.enabled` | bool | 是否启用 Flow Skill |
| `flow_skills.skills` | list | 启用的 Flow Skill 列表 |
| `flow_skills.skills[].name` | string | Skill 名称 |
| `flow_skills.skills[].description` | string | Skill 描述 |

---

## 5. 运行时加载

```python
class PromptBuilder:
    def __init__(self, config: AgentConfig):
        self.flow_skill_loader = FlowSkillLoader()
    
    def build(self, base_prompt: str, flow_skills_config: dict) -> str:
        # 1. 加载 Flow Skill 指令
        flow_skills_content = ""
        if flow_skills_config.get("enabled"):
            for skill_name in flow_skills_config.get("skills", []):
                skill = await self.flow_skill_loader.load(skill_name["name"])
                flow_skills_content += f"\n## {skill.name}\n{skill.instructions}\n"
        
        # 2. 替换占位符
        return base_prompt.replace("${flow_skills}", flow_skills_content)
```

---

## 6. Flow Skill 格式

```yaml
# skills/code-review/flow.yaml
name: code-review
description: "代码审查流程"
trigger:
  patterns:
    - "review"
    - "pr"
    - "审查"

instructions: |
  ## 代码审查 Flow
  
  1. 收集信息
     - 获取代码变更
     - 理解需求背景
  
  2. 执行审查
     - 检查代码质量
     - 检查安全风险
     - 检查性能问题
  
  3. 生成报告
     - 汇总问题
     - 提供改进建议
  
  4. 返回结果
     - 提供审查总结
     - 列出需要修改的问题
```

---

## 7. 目录结构

```
src/young/
├── agent/               # Agent 主类
├── subagent/           # SubAgent 系统
├── flow/                # FlowSkill
│   ├── base.py         # FlowSkill 基类
│   ├── sequential.py    # SequentialFlow
│   ├── parallel.py     # ParallelFlow
│   ├── conditional.py   # ConditionalFlow
│   ├── loop.py        # LoopFlow
│   └── builtins/      # 内置 Flow Skills
├── session/            # Session 管理
├── loader/             # 配置加载
└── ...
```

---

*本文档定义 YoungAgent Flow Skill 设计*

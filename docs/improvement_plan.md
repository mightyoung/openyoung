# OpenYoung 项目改善计划

## 项目背景

### 核心定位
1. **Agent 复制系统**：从 GitHub 快速导入高质量 Agent（Skills、MCPs、Hooks、Evaluations）
2. **FlowSkill**：用 Skill 代替传统 Workflow，低成本执行固定工作流

### 当前问题优先级

| 优先级 | 问题 | 影响 |
|--------|------|------|
| P0 | 超时问题 | Agent 无法完成复杂任务 |
| P1 | FlowSkill 编排能力弱 | 无法有效组织多任务 |
| P2 | GitHub 导入完整性 | 导入的 Agent 不可用 |
| P3 | 模板市场缺失 | 用户无法发现优质模板 |

---

## Phase 1: 解决超时问题 (P0)

### 问题描述
- `young_agent.py:326` 硬编码 `self._max_tool_calls = 10`
- 复杂任务需要 20-50+ 次工具调用
- 导致任务频繁中断

### 解决方案

#### 方案 1.1：支持外部配置（推荐，最小改动）
```python
# young_agent.py 修改
def __init__(self, config):
    # 从配置读取，而非硬编码
    self._max_tool_calls = config.execution.get("max_tool_calls", 10)
```

#### 方案 1.2：基于复杂度自动调整
```python
# 任务复杂度分析
def estimate_complexity(task: str) -> int:
    """根据任务估算所需工具调用次数"""
    indicators = [
        ("创建", 5),      # 创建项目/文件
        ("实现", 10),     # 实现功能
        ("测试", 5),      # 编写测试
        ("爬取", 8),      # 爬虫任务
        ("优化", 6),      # 优化任务
    ]
    base = 10
    for keyword, add in indicators:
        if keyword in task:
            base += add
    return base
```

### 参考案例
- DeerFlow: `SubagentLimitMiddleware` 动态限制
- AutoGen: 基于 token 动态调整

### 里程碑
- [ ] 1.1.1 修改 YoungAgent 支持外部配置
- [ ] 1.1.2 支持 agent.yaml 中配置 max_tool_calls
- [ ] 1.2.1 实现复杂度估算函数
- [ ] 1.2.2 集成到 YoungAgent

---

## Phase 2: 强化 FlowSkill 编排能力 (P1)

### 问题描述
- 当前 FlowSkill 只是简单的 pre/post 处理
- 无法有效组织多个 Skill/Agent 协同工作

### 解决方案

#### 方案 2.1：声明式 Pipeline 定义
```python
@dataclass
class Pipeline:
    stages: List[Stage]
    parallel_groups: List[List[Stage]]
    dependencies: Dict[str, List[str]]

@dataclass
class Stage:
    name: str
    skill: Optional[str]      # 使用的 Skill
    agent: Optional[str]      # 使用的 Agent
    params: Dict[str, Any]   # 参数
    condition: Optional[str]  # 条件执行
```

#### 方案 2.2：扩展 FlowSkill 接口
```python
class FlowSkill(ABC):
    async def get_pipeline(self, task: str) -> Optional[Pipeline]:
        """返回执行管道"""
        return None  # 默认不使用 Pipeline

    async def should_delegate(self, task: str) -> bool:
        """判断是否需要委托"""
        return False

    async def get_subtasks(self, task: str) -> List[SubTask]:
        """分解为子任务"""
        return []
```

### 参考案例
- LangGraph: StateGraph 声明式 DAG
- DeerFlow: Middleware 链式处理

### 里程碑
- [x] 2.1.1 定义 Pipeline 数据结构 ✅
- [x] 2.1.2 实现 Pipeline 执行器 ✅
- [x] 2.2.1 扩展 FlowSkill 接口 ✅
- [x] 2.2.2 创建 CompositeFlowSkill ✅

### 新增文件
- `src/flow/pipeline.py` - Pipeline DAG 编排
- `src/flow/composite.py` - 组合 Skill

### 使用示例
```python
# Pipeline 用法
class MyPipeline(Pipeline):
    def _build(self):
        self.add_stage(Stage(name='stage1', depends_on=[]))
        self.add_stage(Stage(name='stage2', depends_on=['stage1']))

    async def execute_stage(self, stage, context):
        return f'Done: {stage.name}'

# CompositeFlowSkill 用法
from src.flow import compose_skills, compose_parallel

# 链式组合
combined = compose_skills(skill1, skill2, skill3)

# 并行组合
parallel = compose_parallel(skill1, skill2)
```

---

## Phase 3: 完善 GitHub 导入 (P2)

### 问题描述
- 识别了需要的 Skills/MCPs/Hooks
- 但没有实际加载和安装
- 导入的 Agent 不可用

### 解决方案

#### 方案 3.1：依赖解析器
```python
@dataclass
class AgentDependency:
    skill_requirements: List[str]
    mcp_requirements: List[str]
    hook_requirements: List[str]
    missing: List[str]  # 缺失的依赖

def resolve_dependencies(config: dict) -> AgentDependency:
    """解析 Agent 配置中的依赖"""
    # 解析 required_skills
    # 解析 required_mcps
    # 解析 required_hooks
    # 检查已安装
    # 返回缺失列表
```

#### 方案 3.2：自动安装缺失依赖
```python
async def install_missing_dependencies(dep: AgentDependency):
    """安装缺失的依赖"""
    for skill in dep.missing_skills:
        await install_skill(skill)
    for mcp in dep.missing_mcps:
        await install_mcp(mcp)
```

### 参考案例
- npm: package.json 依赖解析
- DeerFlow: 插件自动安装

### 里程碑
- [x] 3.1.1 定义依赖数据结构 ✅
- [x] 3.1.2 实现依赖解析器 ✅
- [x] 3.2.1 实现自动安装逻辑 ✅
- [x] 3.2.2 集成到导入流程 ✅

### 新增文件
- `src/package_manager/dependency_resolver.py` - 依赖解析器
- `src/package_manager/dependency_installer.py` - 依赖安装器

### 使用示例
```python
from src.package_manager import resolve_agent_dependencies, install_agent_dependencies

# 解析依赖
all_deps, missing = resolve_agent_dependencies('packages/my-agent')

# 安装缺失依赖
results = await install_agent_dependencies('packages/my-agent')
```

### 测试结果
```
Agent: agent-everything-claude-code
  - Skills: 18
  - MCPs: 1
  - Missing: 18 skills + 1 MCP
```

---

## Phase 4: 建立模板市场 (P3)

### 问题描述
- 用户无法发现优质 Agent 模板
- 缺少一键安装机制

### 解决方案

#### 方案 4.1：模板注册表
```yaml
# templates/registry.yaml
templates:
  - name: "agent-coder"
    source: "github.com/xxx/agent-coder"
    rating: 4.5
    installs: 1000
    tags: ["coding", "development"]

  - name: "skill-github-import"
    source: "local:skill-github-import"
    rating: 4.8
    tags: ["import", "github"]
```

#### 方案 4.2：CLI 命令
```bash
openyoung templates list          # 列出模板
openyoung templates install xxx  # 安装模板
openyoung templates submit xxx   # 提交模板
```

### 里程碑
- [x] 4.1.1 创建模板注册表 ✅
- [x] 4.1.2 实现模板发现服务 ✅
- [x] 4.2.1 添加 CLI 命令 ✅
- [x] 4.2.2 实现评分/排名 ✅

### 新增文件
- `src/package_manager/template_registry.py` - 模板注册表
- `templates/registry.yaml` - 模板数据存储

### CLI 命令
```bash
openyoung templates list              # 列出模板
openyoung templates search <query>    # 搜索模板
openyoung templates add <name> <source> # 添加模板
openyoung templates remove <name>     # 移除模板
openyoung templates info <name>       # 查看模板详情
```

### 测试结果
```
Found 6 templates:
  - agent-coder
  - agent-reviewer
  - agent-researcher
  - skill-github-import
  - skill-eval-planner
  - skill-tdd-workflow
```

---

## 执行顺序建议

```
Phase 1 (P0): 立即开始
    ↓
Phase 2 (P1): Phase 1 完成后
    ↓
Phase 3 (P2): Phase 2 完成后
    ↓
Phase 4 (P3): 可并行进行
```

---

## 预期效果

| Phase | 效果 |
|-------|------|
| Phase 1 | 复杂任务可完成，不再频繁中断 |
| Phase 2 | 可有效组织多 Agent 协同工作 |
| Phase 3 | 导入的 Agent 可直接使用 |
| Phase 4 | 用户可发现和安装优质模板 |

---

## 风险与缓解

| 风险 | 缓解措施 |
|------|----------|
| 改动过大影响现有功能 | 每个 Phase 设置验收测试 |
| 复杂度估算不准确 | 提供手动覆盖选项 |
| 依赖解析出错 | 记录日志，支持回滚 |

---

*创建日期: 2026-03-05*
*最后更新: 2026-03-05*

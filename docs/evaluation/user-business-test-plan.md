# OpenYoung 用户业务测试计划

> **目标:** 验证 OpenYoung 系统所有业务功能是否按设计实现并正常工作

**测试范围:** 11个核心模块的所有业务功能点

**测试方法:** 黑盒功能测试 + 集成测试

---

## 1. 演化机制 (Evolution Mechanism)

### Task 1.1: Evolver 基础功能测试

**测试文件:**
- 测试: `tests/evolver/test_evolver_basic.py`

**Step 1: 编写测试用例**

```python
import pytest
from src.evolver.models import EvolverConfig, EvolutionResult
from src.evolver.evolver import Evolver

def test_evolver_initialization():
    """测试 Evolver 初始化"""
    config = EvolverConfig(
        population_size=10,
        generations=5,
        mutation_rate=0.1
    )
    evolver = Evolver(config)
    assert evolver.config.population_size == 10
    assert evolver.current_generation == 0

def test_evolver_evolve_single_generation():
    """测试单代演化"""
    config = EvolverConfig(population_size=5, generations=3)
    evolver = Evolver(config)
    initial_population = evolver.population.copy()
    
    result = evolver.evolve()
    
    assert result.generation == 1
    assert len(evolvers.population) == 5
    assert result.best_fitness >= initial_population[0].fitness

def test_evolver_mutation_operator():
    """测试变异操作"""
    # 测试变异率是否正常工作
    pass

def test_evolver_crossover_operator():
    """测试交叉操作"""
    # 测试交叉是否产生有效后代
    pass
```

**Step 2: 运行测试**

```bash
pytest tests/evolver/test_evolver_basic.py -v
```

---

### Task 1.2: 演化结果评估测试

**测试文件:**
- 测试: `tests/evolver/test_evolution_result.py`

**测试点:**
- 演化历史记录完整性
- 最佳个体追踪
- 收敛判断
- 早停机制

---

## 2. Harness 运行时状态 (Harness Runtime Status)

### Task 2.1: Harness 生命周期测试

**测试文件:**
- 测试: `tests/harness/test_harness_lifecycle.py`

**Step 1: 编写测试用例**

```python
from src.harness.harness import Harness, HarnessStatus

def test_harness_initialization():
    """测试 Harness 初始化状态"""
    harness = Harness()
    assert harness.status == HarnessStatus.IDLE
    assert harness.start_time is None

def test_harness_start():
    """测试 Harness 启动"""
    harness = Harness()
    harness.start()
    assert harness.status == HarnessStatus.RUNNING
    assert harness.start_time is not None

def test_harness_pause():
    """测试 Harness 暂停"""
    harness = Harness()
    harness.start()
    harness.pause()
    assert harness.status == HarnessStatus.PAUSED

def test_harness_stop():
    """测试 Harness 停止"""
    harness = Harness()
    harness.start()
    result = harness.stop()
    assert harness.status == HarnessStatus.STOPPED
    assert result.total_steps > 0
```

**Step 2: 运行测试**

```bash
pytest tests/harness/test_harness_lifecycle.py -v
```

---

### Task 2.2: Harness 状态监控测试

**测试文件:**
- 测试: `tests/harness/test_harness_monitoring.py`

**测试点:**
- 实时状态查询
- 性能指标收集
- 资源使用监控
- 错误状态捕获

---

## 3. 知识蒸馏 (Knowledge Distillation)

### Task 3.1: 知识提取测试

**测试文件:**
- 测试: `tests/distillation/test_knowledge_extraction.py`

```python
from src.distillation.distiller import KnowledgeDistiller

def test_distiller_extract_from_agent():
    """测试从 Agent 提取知识"""
    distiller = KnowledgeDistiller()
    agent = YoungAgent(...)
    
    knowledge = distiller.extract(agent)
    
    assert knowledge.experience_count > 0
    assert knowledge.patterns is not None
    assert len(knowledge.key_insights) > 0

def test_distiller_extract_from_execution():
    """测试从执行历史提取知识"""
    distiller = KnowledgeDistiller()
    execution_history = [...]
    
    knowledge = distiller.extract_from_history(execution_history)
    
    assert knowledge.action_patterns is not None
    assert knowledge.success_patterns is not None
```

---

### Task 3.2: 知识压缩测试

**测试文件:**
- 测试: `tests/distillation/test_knowledge_compression.py`

**测试点:**
- 知识表示压缩
- 重要知识保留
- 蒸馏损失评估

---

## 4. Skill 加载 (Skill Loading)

### Task 4.1: Skill 注册与发现

**测试文件:**
- 测试: `tests/skills/test_skill_registration.py`

```python
from src.skills.skill_manager import SkillManager, Skill

def test_skill_manager_register():
    """测试 Skill 注册"""
    manager = SkillManager()
    skill = Skill(name="test_skill", handler=...)
    
    manager.register(skill)
    assert "test_skill" in manager.list_skills()

def test_skill_manager_discover():
    """测试 Skill 自动发现"""
    manager = SkillManager()
    skills = manager.discover_skills("src/skills/")
    
    assert len(skills) > 0

def test_skill_manager_load():
    """测试 Skill 加载"""
    manager = SkillManager()
    skill = manager.load("writing-plans")
    
    assert skill is not None
    assert skill.is_loaded()
```

---

### Task 4.2: Skill 执行测试

**测试文件:**
- 测试: `tests/skills/test_skill_execution.py`

**测试点:**
- Skill 正确执行
- Skill 隔离执行
- Skill 超时处理
- Skill 错误传播

---

## 5. MCP 加载 (MCP Loading)

### Task 5.1: MCP Server 连接测试

**测试文件:**
- 测试: `tests/mcp/test_mcp_connection.py`

```python
from src.mcp.mcp_client import MCPClient, MCPServer

def test_mcp_server_connection():
    """测试 MCP Server 连接"""
    server = MCPServer("http://localhost:8080")
    client = MCPClient(server)
    
    assert client.connect()
    assert client.is_connected()

def test_mcp_list_tools():
    """测试列出可用工具"""
    client = MCPClient(...)
    tools = client.list_tools()
    
    assert len(tools) > 0

def test_mcp_call_tool():
    """测试调用工具"""
    client = MCPClient(...)
    result = client.call_tool("web_search", {"query": "test"})
    
    assert result is not None
```

---

### Task 5.2: MCP 工具映射测试

**测试文件:**
- 测试: `tests/mcp/test_mcp_tool_mapping.py`

**测试点:**
- 工具名称映射
- 参数类型转换
- 返回值解析

---

## 6. Agent 执行 (Agent Execution)

### Task 6.1: YoungAgent 基础执行

**测试文件:**
- 测试: `tests/agents/test_young_agent_execution.py`

```python
from src.agents.young_agent import YoungAgent

def test_agent_initialization():
    """测试 Agent 初始化"""
    agent = YoungAgent(name="test_agent")
    assert agent.name == "test_agent"
    assert agent.status == "idle"

def test_agent_execute_task():
    """测试 Agent 执行任务"""
    agent = YoungAgent(name="test_agent")
    result = agent.execute("写一个Hello World程序")
    
    assert result.success
    assert result.output is not None

def test_agent_stream_execution():
    """测试流式执行"""
    agent = YoungAgent(name="test_agent")
    chunks = list(agent.execute_stream("计算1+1"))
    
    assert len(chunks) > 0
    assert "2" in "".join(chunks)
```

---

### Task 6.2: Agent 状态管理

**测试文件:**
- 测试: `tests/agents/test_agent_state.py`

**测试点:**
- 状态转换正确性
- 上下文保持
- 资源清理

---

## 7. Subagent 调用 (Subagent Invocation)

### Task 7.1: Subagent 创建与调度

**测试文件:**
- 测试: `tests/agents/test_subagent_invocation.py`

```python
from src.agents.dispatcher import AgentDispatcher

def test_dispatcher_create_subagent():
    """测试创建 Subagent"""
    dispatcher = AgentDispatcher()
    subagent = dispatcher.create_subagent(
        parent_id="agent_1",
        task_type="research"
    )
    
    assert subagent.parent_id == "agent_1"
    assert subagent.task_type == "research"

def test_dispatcher_route_task():
    """测试任务路由"""
    dispatcher = AgentDispatcher()
    result = dispatcher.route_task("分析代码质量")
    
    assert result.subagent_id is not None
    assert result.routing_reason is not None
```

---

### Task 7.2: Subagent 通信

**测试文件:**
- 测试: `tests/agents/test_subagent_communication.py`

**测试点:**
- 父子 Agent 消息传递
- 结果汇总
- 超时处理

---

## 8. 评估机制 (Evaluation Mechanism)

### Task 8.1: Evaluation Hub 基本功能

**测试文件:**
- 测试: `tests/evaluation/test_evaluation_hub.py`

```python
from src.evaluation.hub import EvaluationHub, EvaluationCriteria

def test_evaluation_hub_initialization():
    """测试评估中心初始化"""
    hub = EvaluationHub()
    assert hub.is_ready()

def test_evaluate_agent_response():
    """测试 Agent 响应评估"""
    hub = EvaluationHub()
    result = hub.evaluate(
        response="这是一个测试响应",
        criteria=EvaluationCriteria.ACCURACY
    )
    
    assert result.score is not None
    assert 0 <= result.score <= 1

def test_evaluate_multiple_criteria():
    """测试多维度评估"""
    hub = EvaluationHub()
    results = hub.evaluate_comprehensive(
        response="测试响应",
        criteria_list=[
            EvaluationCriteria.ACCURACY,
            EvaluationCriteria.COHERENCE,
            EvaluationCriteria.SAFETY
        ]
    )
    
    assert len(results) == 3
```

---

### Task 8.2: 评估指标计算

**测试文件:**
- 测试: `tests/evaluation/test_evaluation_metrics.py`

**测试点:**
- 准确率计算
- 一致性计算
- 安全性检测
- 自定义指标

---

## 9. 包管理 (Package Management)

### Task 9.1: 包安装测试

**测试文件:**
- 测试: `tests/package_manager/test_package_install.py`

```python
from src.package_manager.manager import PackageManager

def test_install_from_pypi():
    """测试从 PyPI 安装"""
    manager = PackageManager()
    result = manager.install("requests")
    
    assert result.success
    assert manager.is_installed("requests")

def test_install_from_source():
    """测试从源码安装"""
    manager = PackageManager()
    result = manager.install_from_source("https://github.com/user/repo.git")
    
    assert result.success
```

---

### Task 9.2: 包卸载与源加载

**测试文件:**
- 测试: `tests/package_manager/test_package_operations.py`

```python
def test_uninstall_package():
    """测试卸载包"""
    manager = PackageManager()
    manager.install("numpy")
    
    result = manager.uninstall("numpy")
    
    assert result.success
    assert not manager.is_installed("numpy")

def test_load_package_source():
    """测试加载包源码"""
    manager = PackageManager()
    source = manager.load_source("openyoung")
    
    assert source is not None
    assert "setup.py" in source.files
```

---

## 10. Agent 配置 (Agent Configuration)

### Task 10.1: 配置加载测试

**测试文件:**
- 测试: `tests/config/test_config_loading.py`

```python
from src.config.loader import ConfigLoader

def test_load_yaml_config():
    """测试 YAML 配置加载"""
    loader = ConfigLoader()
    config = loader.load("config/agent.yaml")
    
    assert config.agent_name is not None
    assert config.model is not None

def test_load_json_config():
    """测试 JSON 配置加载"""
    loader = ConfigLoader()
    config = loader.load("config/agent.json")
    
    assert config is not None
```

---

### Task 10.2: 配置验证测试

**测试文件:**
- 测试: `tests/config/test_config_validation.py`

**测试点:**
- 必填字段验证
- 类型验证
- 值范围验证
- 默认值应用

---

## 11. 集成测试

### Task 11.1: 端到端业务流程测试

**测试文件:**
- 测试: `tests/integration/test_e2e_business.py`

```python
def test_full_agent_workflow():
    """完整业务流程测试"""
    # 1. 初始化 Agent
    agent = YoungAgent(name="workflow_agent")
    
    # 2. 加载配置
    config = loader.load("config/default.yaml")
    agent.configure(config)
    
    # 3. 执行任务
    result = agent.execute("分析项目代码质量")
    
    # 4. 评估结果
    evaluation = hub.evaluate(result.output)
    
    # 5. 验证
    assert result.success
    assert evaluation.score > 0.5
```

---

### Task 11.2: 多 Agent 协作测试

**测试文件:**
- 测试: `tests/integration/test_multi_agent.py`

**测试点:**
- 多 Agent 任务分发
- Agent 间通信
- 结果汇总

---

## 测试执行命令

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定模块测试
pytest tests/evolver/ -v
pytest tests/harness/ -v
pytest tests/agents/ -v

# 运行集成测试
pytest tests/integration/ -v

# 生成测试报告
pytest tests/ --html=report.html --self-contained-html
```

---

## 验收标准

- [ ] 所有 11 个模块的功能测试用例编写完成
- [ ] 单元测试覆盖率 > 80%
- [ ] 集成测试覆盖主要业务流程
- [ ] 所有测试用例通过
- [ ] 测试文档完整

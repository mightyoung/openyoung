"""
Context Collector - 完整上下文收集器

收集完整的过程数据用于可观测性:
- Agent 配置
- Skills 加载状态
- MCP 服务器配置
- Hooks 执行状态
- 网络连接状态
- Subagent 执行记录
- 评估结果
- 自迭代循环
- Evolver 演进记录
"""

import json
import os
import socket
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class SkillInfo:
    """Skill 信息"""

    name: str
    path: str
    version: Optional[str] = None
    enabled: bool = True


@dataclass
class McpInfo:
    """MCP 服务器信息"""

    name: str
    command: str
    args: List[str] = field(default_factory=list)
    env: Dict[str, str] = field(default_factory=dict)


@dataclass
class HookInfo:
    """Hook 信息"""

    name: str
    hook_type: str
    enabled: bool = True
    last_executed: Optional[str] = None
    result: Optional[str] = None


@dataclass
class ConnectionInfo:
    """网络连接信息"""

    target: str
    port: Optional[int] = None
    protocol: str = "tcp"
    status: str = "unknown"
    bytes_sent: int = 0
    bytes_received: int = 0


@dataclass
class NetworkStatus:
    """网络状态"""

    connected: bool
    connections: List[ConnectionInfo] = field(default_factory=list)


@dataclass
class SubAgentExecution:
    """Sub-agent 执行记录"""

    agent_id: str
    agent_name: str
    task: str
    start_time: str
    end_time: Optional[str] = None
    status: str = "pending"
    result: Optional[str] = None
    iterations: int = 0


@dataclass
class EvaluationResult:
    """评估结果"""

    metric: str
    score: float
    reasoning: str
    timestamp: str


@dataclass
class IterationRecord:
    """自迭代记录"""

    iteration: int
    timestamp: str
    input: str
    output: str
    evaluation: Optional[EvaluationResult] = None
    feedback: str = ""
    improved: bool = False


@dataclass
class GeneInfo:
    """Evolver 基因信息"""

    gene_id: str
    version: str = "1.0.0"
    category: str = "repair"
    signals: List[str] = field(default_factory=list)
    preconditions: List[str] = field(default_factory=list)
    strategy: List[str] = field(default_factory=list)
    success_rate: float = 0.0
    usage_count: int = 0


@dataclass
class CapsuleInfo:
    """Evolver 执行单元信息"""

    capsule_id: str
    name: str = ""
    description: str = ""
    trigger: List[str] = field(default_factory=list)
    gene_ref: str = ""
    gene_version: str = ""
    summary: str = ""
    created_at: str = ""


@dataclass
class EvolutionEventInfo:
    """Evolver 演进事件记录"""

    event_id: str
    event_type: str
    description: str
    timestamp: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EvolverExecution:
    """Evolver 演进执行记录"""

    engine_id: str
    status: str = "idle"
    genes: List[GeneInfo] = field(default_factory=list)
    capsules: List[CapsuleInfo] = field(default_factory=list)
    events: List[EvolutionEventInfo] = field(default_factory=list)
    selected_gene: Optional[str] = None


@dataclass
class AgentContext:
    """完整的 Agent 上下文"""

    request_id: str
    timestamp: str
    agent_id: str
    agent_name: str
    agent_repo_url: str

    # 配置
    skills: List[SkillInfo] = field(default_factory=list)
    mcps: List[McpInfo] = field(default_factory=list)
    hooks: List[HookInfo] = field(default_factory=list)

    # 环境
    environment_vars: Dict[str, str] = field(default_factory=dict)
    network_status: Optional[NetworkStatus] = None

    # 执行轨迹
    subagent_executions: List[SubAgentExecution] = field(default_factory=list)
    evaluation_results: List[EvaluationResult] = field(default_factory=list)
    iteration_history: List[IterationRecord] = field(default_factory=list)

    # Evolver 演进记录
    evolver_executions: List[EvolverExecution] = field(default_factory=list)


class ContextCollector:
    """上下文收集器"""

    def __init__(self, agent_id: str = "default", agent_name: str = "default"):
        self.agent_id = agent_id
        self.agent_name = agent_name
        self.context = AgentContext(
            request_id=self._generate_request_id(),
            timestamp=datetime.now().isoformat(),
            agent_id=agent_id,
            agent_name=agent_name,
            agent_repo_url="",
        )

    def _generate_request_id(self) -> str:
        """生成请求 ID"""
        import uuid

        return str(uuid.uuid4())

    def set_repo_url(self, url: str):
        """设置 Agent 仓库 URL"""
        self.context.agent_repo_url = url

    def collect_skills(self, skills_dir: str = None) -> List[SkillInfo]:
        """收集已加载的 Skills"""
        if skills_dir is None:
            skills_dir = os.path.join(os.getcwd(), "skills")

        skills = []
        skills_path = Path(skills_dir)

        if skills_path.exists():
            for skill_file in skills_path.glob("*.md"):
                skills.append(
                    SkillInfo(
                        name=skill_file.stem,
                        path=str(skill_file),
                        enabled=True,
                    )
                )

        self.context.skills = skills
        return skills

    def collect_mcps(self, mcp_config_path: str = None) -> List[McpInfo]:
        """收集 MCP 配置"""
        mcps = []

        if mcp_config_path is None:
            mcp_config_path = os.path.join(os.getcwd(), ".mcp.json")

        mcp_path = Path(mcp_config_path)
        if mcp_path.exists():
            try:
                with open(mcp_path) as f:
                    mcp_config = json.load(f)
                    for mcp in mcp_config.get("mcp_servers", {}).values():
                        mcps.append(
                            McpInfo(
                                name=mcp.get("name", "unknown"),
                                command=mcp.get("command", ""),
                                args=mcp.get("args", []),
                                env=mcp.get("env", {}),
                            )
                        )
            except Exception as e:
                logger.debug(f"Failed to collect MCP info: {e}")

        self.context.mcps = mcps
        return mcps

    def collect_hooks(self, settings_path: str = None) -> List[HookInfo]:
        """收集 Hooks 配置"""
        hooks = []

        if settings_path is None:
            settings_path = os.path.join(os.getcwd(), ".claude", "settings.json")

        settings_file = Path(settings_path)
        if settings_file.exists():
            try:
                with open(settings_file) as f:
                    settings = json.load(f)
                    hooks_config = settings.get("hooks", {})

                    for hook_type, hook_list in hooks_config.items():
                        if isinstance(hook_list, list):
                            for hook in hook_list:
                                hooks.append(
                                    HookInfo(
                                        name=hook.get("matcher", hook_type),
                                        hook_type=hook_type,
                                        enabled=True,
                                    )
                                )
            except Exception as e:
                logger.debug(f"Failed to collect hook info: {e}")

        self.context.hooks = hooks
        return hooks

    def collect_environment_vars(self, prefix: str = None) -> Dict[str, str]:
        """收集环境变量"""
        env_vars = {}

        # 收集相关环境变量
        prefixes = ["CLAUDE_", "OPENAI_", "ANTHROPIC_", "IRONCLAW_"]
        if prefix:
            prefixes = [prefix]

        for key, value in os.environ.items():
            for p in prefixes:
                if key.startswith(p):
                    # 隐藏敏感值
                    if "KEY" in key or "SECRET" in key or "TOKEN" in key:
                        env_vars[key] = "***REDACTED***"
                    else:
                        env_vars[key] = value

        self.context.environment_vars = env_vars
        return env_vars

    def collect_network_status(self) -> NetworkStatus:
        """收集网络状态"""
        connections = []

        # 检查外部连接
        test_hosts = [
            ("api.openai.com", 443),
            ("api.anthropic.com", 443),
            ("github.com", 443),
        ]

        connected = False
        for host, port in test_hosts:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            try:
                result = sock.connect_ex((host, port))
                if result == 0:
                    connected = True
                    connections.append(
                        ConnectionInfo(
                            target=host,
                            port=port,
                            protocol="tcp",
                            status="connected",
                        )
                    )
            except Exception as e:
                logger.debug(f"Failed to check connection to {host}: {e}")
            finally:
                sock.close()

        status = NetworkStatus(connected=connected, connections=connections)
        self.context.network_status = status
        return status

    def add_subagent_execution(self, execution: SubAgentExecution):
        """添加 subagent 执行记录"""
        self.context.subagent_executions.append(execution)

    def add_evaluation_result(self, result: EvaluationResult):
        """添加评估结果"""
        self.context.evaluation_results.append(result)

    def add_iteration(self, iteration: IterationRecord):
        """添加自迭代记录"""
        self.context.iteration_history.append(iteration)

    def add_evolver_execution(self, execution: EvolverExecution):
        """添加 Evolver 演进执行记录"""
        self.context.evolver_executions.append(execution)

    def collect_evolver_data(self, engine) -> EvolverExecution:
        """从 EvolutionEngine 收集演进数据"""
        execution = EvolverExecution(
            engine_id=f"evolver_{self._generate_request_id()[:8]}",
            status="active",
        )

        # 收集基因信息
        if hasattr(engine, "_matcher") and hasattr(engine._matcher, "_genes"):
            for gene_id, gene in engine._matcher._genes.items():
                gene_info = GeneInfo(
                    gene_id=gene.id,
                    version=gene.version,
                    category=gene.category.value
                    if hasattr(gene.category, "value")
                    else str(gene.category),
                    signals=gene.signals,
                    preconditions=gene.preconditions,
                    strategy=gene.strategy,
                    success_rate=gene.success_rate,
                    usage_count=gene.usage_count,
                )
                execution.genes.append(gene_info)

        # 收集执行单元信息
        if hasattr(engine, "_capsules"):
            for capsule_id, capsule in engine._capsules.items():
                capsule_info = CapsuleInfo(
                    capsule_id=capsule.id,
                    name=capsule.name,
                    description=capsule.description,
                    trigger=capsule.trigger,
                    gene_ref=capsule.gene_ref,
                    gene_version=capsule.gene_version,
                    summary=capsule.summary,
                    created_at=capsule.created_at.isoformat() if capsule.created_at else "",
                )
                execution.capsules.append(capsule_info)

        # 收集演进事件
        if hasattr(engine, "_events"):
            for event in engine._events:
                event_info = EvolutionEventInfo(
                    event_id=event.id,
                    event_type=event.event_type.value
                    if hasattr(event.event_type, "value")
                    else str(event.event_type),
                    description=event.description,
                    timestamp=event.timestamp.isoformat()
                    if event.timestamp
                    else datetime.now().isoformat(),
                    metadata=event.metadata,
                )
                execution.events.append(event_info)

        self.context.evolver_executions.append(execution)
        return execution

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self.context)

    def to_json(self) -> str:
        """转换为 JSON"""
        return json.dumps(self.to_dict(), indent=2, default=str)


def create_context_collector(
    agent_id: str = "default",
    agent_name: str = "default",
    repo_url: str = None,
) -> ContextCollector:
    """创建上下文收集器"""
    collector = ContextCollector(agent_id, agent_name)

    if repo_url:
        collector.set_repo_url(repo_url)

    # 自动收集
    collector.collect_skills()
    collector.collect_mcps()
    collector.collect_hooks()
    collector.collect_environment_vars()
    collector.collect_network_status()

    return collector


if __name__ == "__main__":
    # 测试
    collector = create_context_collector(
        agent_id="agenticSeek",
        agent_name="Jarvis",
        repo_url="https://github.com/Fosowl/agenticSeek",
    )
    print(collector.to_json())

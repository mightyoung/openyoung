"""
Agent Metadata Schema - Agent 元数据结构定义

定义 4 级渐进式元数据结构:
- Level 1: Basic (name, description, badges)
- Level 2: Capabilities + Skills
- Level 3: Orchestration
- Level 4: Performance
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class AgentTier(Enum):
    """Agent 层级"""

    FOUNDATION = "foundation"  # 基础 Agent
    SPECIALIZED = "specialized"  # 专业 Agent
    ORCHESTRATOR = "orchestrator"  # 编排 Agent


class MetadataLevel(Enum):
    """元数据加载层级"""

    LEVEL_1_BASIC = 1  # 基础信息
    LEVEL_2_CAPABILITIES = 2  # 能力和技能
    LEVEL_3_ORCHESTRATION = 3  # 编排配置
    LEVEL_4_PERFORMANCE = 4  # 性能指标


@dataclass
class AgentCapability:
    """Agent 能力"""

    name: str  # 能力名称
    description: str  # 能力描述
    category: str  # 类别 (coding, research, analysis, etc.)
    keywords: list[str] = field(default_factory=list)


@dataclass
class SkillDefinition:
    """技能定义"""

    skill_id: str  # 技能 ID
    name: str  # 技能名称
    description: str  # 技能描述
    type: str  # 技能类型 (tool, prompt, workflow)
    input_schema: dict[str, Any] = field(default_factory=dict)
    output_schema: dict[str, Any] = field(default_factory=dict)
    examples: list[str] = field(default_factory=list)


@dataclass
class SubAgentConfig:
    """子 Agent 配置"""

    agent_id: str  # 子 Agent ID
    role: str  # 角色
    description: str  # 描述
    max_retries: int = 3
    timeout: float = 300.0


@dataclass
class CompatibilityInfo:
    """兼容性信息"""

    required_skills: list[str] = field(default_factory=list)
    incompatible_agents: list[str] = field(default_factory=list)
    min_context_length: int = 8192
    max_context_length: int = 200000


@dataclass
class PerformanceMetrics:
    """性能指标"""

    success_rate: float = 0.0  # 成功率 (0-1)
    avg_execution_time: float = 0.0  # 平均执行时间 (秒)
    throughput: float = 0.0  # 吞吐量 (任务/分钟)
    error_rate: float = 0.0  # 错误率 (0-1)


@dataclass
class AgentMetadata:
    """完整 Agent 元数据

    支持渐进式披露，按需加载不同层级的元数据。
    """

    # Level 1 - Basic (Always loaded)
    agent_id: str
    name: str
    description: str
    version: str = "1.0.0"
    source_repo: str = ""
    tier: AgentTier = AgentTier.SPECIALIZED
    badges: list[str] = field(default_factory=list)

    # Level 2 - Capabilities (On selection)
    capabilities: list[AgentCapability] = field(default_factory=list)
    skills: list[SkillDefinition] = field(default_factory=list)
    compatibility: Optional[CompatibilityInfo] = None

    # Level 3 - Orchestration (On assignment)
    subagents: list[SubAgentConfig] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    max_context_length: int = 8192

    # Level 4 - Performance (On evaluation)
    performance: Optional[PerformanceMetrics] = None
    evaluation_scores: dict[str, float] = field(default_factory=dict)
    last_evaluated: Optional[datetime] = None

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    loaded_level: MetadataLevel = MetadataLevel.LEVEL_1_BASIC

    def get_capability_names(self) -> list[str]:
        """获取所有能力名称"""
        return [c.name for c in self.capabilities]

    def get_skill_ids(self) -> list[str]:
        """获取所有技能 ID"""
        return [s.skill_id for s in self.skills]

    def has_skill(self, skill_id: str) -> bool:
        """检查是否有特定技能"""
        return skill_id in self.get_skill_ids()

    def upgrade_level(self, target_level: MetadataLevel) -> bool:
        """升级元数据加载层级

        Args:
            target_level: 目标层级

        Returns:
            是否成功升级
        """
        if target_level.value <= self.loaded_level.value:
            return False

        self.loaded_level = target_level
        self.updated_at = datetime.now()
        return True

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "source_repo": self.source_repo,
            "tier": self.tier.value,
            "badges": self.badges,
            "capabilities": [
                {"name": c.name, "description": c.description, "category": c.category}
                for c in self.capabilities
            ],
            "skills": [s.skill_id for s in self.skills],
            "loaded_level": self.loaded_level.value,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AgentMetadata":
        """从字典创建"""
        tier = AgentTier(data.get("tier", "specialized"))
        return cls(
            agent_id=data["agent_id"],
            name=data["name"],
            description=data.get("description", ""),
            version=data.get("version", "1.0.0"),
            source_repo=data.get("source_repo", ""),
            tier=tier,
            badges=data.get("badges", []),
        )


# ============================================================================
# Convenience Functions
# ============================================================================


def create_basic_metadata(
    agent_id: str,
    name: str,
    description: str,
    tier: AgentTier = AgentTier.SPECIALIZED,
) -> AgentMetadata:
    """创建基础元数据"""
    return AgentMetadata(
        agent_id=agent_id,
        name=name,
        description=description,
        tier=tier,
    )

"""
Contract types for PEAS
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

# Import Priority from document module
from .document import Priority


@dataclass
class ContractRequirement:
    """合约需求"""

    req_id: str  # "REQ-001"
    description: str
    priority: Priority
    verification_method: str  # "llm_judge" / "regex" / "manual"
    verification_prompt: Optional[str] = None
    metadata: dict = field(default_factory=dict)

    def __str__(self) -> str:
        return f"ContractRequirement({self.req_id}: {self.verification_method})"


@dataclass
class IntentSpec:
    """意图规格"""

    primary_goals: list[str] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)
    quality_bar: str = "default"
    metadata: dict = field(default_factory=dict)

    def __str__(self) -> str:
        return f"IntentSpec({len(self.primary_goals)} goals)"


@dataclass
class ExecutionContract:
    """执行合约"""

    contract_id: str
    version: str
    created_at: datetime
    requirements: list[ContractRequirement]
    metadata: dict = field(default_factory=dict)
    intent: Optional[IntentSpec] = None

    @classmethod
    def create(
        cls,
        requirements: list[ContractRequirement],
        intent: Optional[IntentSpec] = None,
        version: str = "1.0",
        metadata: dict = None,
    ) -> "ExecutionContract":
        """创建合约的工厂方法"""
        return cls(
            contract_id=str(uuid.uuid4()),
            version=version,
            created_at=datetime.now(),
            requirements=requirements,
            metadata=metadata or {},
            intent=intent,
        )

    def get_requirement(self, req_id: str) -> ContractRequirement:
        """获取指定ID的需求"""
        for req in self.requirements:
            if req.req_id == req_id:
                return req
        raise ValueError(f"Requirement {req_id} not found")

    @property
    def total_requirements(self) -> int:
        return len(self.requirements)

    def __str__(self) -> str:
        return f"ExecutionContract({self.contract_id[:8]}, {self.total_requirements} requirements)"

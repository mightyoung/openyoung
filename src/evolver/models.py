"""
Evolver - Self-evolution system
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class GeneCategory(str, Enum):
    REPAIR = "repair"
    OPTIMIZE = "optimize"
    INNOVATE = "innovate"


class EvolutionEventType(str, Enum):
    GENE_UPDATE = "gene_update"
    CAPSULE_CREATE = "capsule_create"
    PERSONALITY_CHANGE = "personality_change"


@dataclass
class Gene:
    id: str
    version: str = "1.0.0"
    category: GeneCategory = GeneCategory.REPAIR
    signals: list[str] = field(default_factory=list)
    preconditions: list[str] = field(default_factory=list)
    strategy: list[str] = field(default_factory=list)
    constraints: dict[str, Any] = field(default_factory=dict)
    validation: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    success_rate: float = 0.0
    usage_count: int = 0


@dataclass
class Capsule:
    id: str
    name: str = ""
    description: str = ""
    trigger: list[str] = field(default_factory=list)
    gene_ref: str = ""
    gene_version: str = ""
    summary: str = ""
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class EvolutionEvent:
    id: str
    event_type: EvolutionEventType
    description: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Personality:
    name: str
    traits: dict[str, float] = field(default_factory=dict)
    genes: list[str] = field(default_factory=list)

    def update_trait(self, trait: str, value: float):
        self.traits[trait] = max(0.0, min(1.0, value))

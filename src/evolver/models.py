"""
Evolver - Self-evolution system
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum


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
    signals: List[str] = field(default_factory=list)
    preconditions: List[str] = field(default_factory=list)
    strategy: List[str] = field(default_factory=list)
    constraints: Dict[str, Any] = field(default_factory=dict)
    validation: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    success_rate: float = 0.0
    usage_count: int = 0


@dataclass
class Capsule:
    id: str
    name: str = ""
    description: str = ""
    trigger: List[str] = field(default_factory=list)
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
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Personality:
    name: str
    traits: Dict[str, float] = field(default_factory=dict)
    genes: List[str] = field(default_factory=list)

    def update_trait(self, trait: str, value: float):
        self.traits[trait] = max(0.0, min(1.0, value))

"""
Evolver - Self-evolution system
"""

from .models import (
    Gene,
    Capsule,
    EvolutionEvent,
    Personality,
    GeneCategory,
    EvolutionEventType,
)
from .engine import (
    EvolutionEngine,
    GeneMatcher,
    PersonalityManager,
    create_evolution_engine,
)

__all__ = [
    "Gene",
    "Capsule",
    "EvolutionEvent",
    "Personality",
    "GeneCategory",
    "EvolutionEventType",
    "EvolutionEngine",
    "GeneMatcher",
    "PersonalityManager",
    "create_evolution_engine",
]

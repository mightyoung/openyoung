"""
Evolver - Self-evolution system
"""

from .engine import (
    EvolutionEngine,
    GeneMatcher,
    PersonalityManager,
    create_evolution_engine,
)
from .models import (
    Capsule,
    EvolutionEvent,
    EvolutionEventType,
    Gene,
    GeneCategory,
    Personality,
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

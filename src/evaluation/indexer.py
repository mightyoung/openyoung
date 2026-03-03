"""
Evaluation Index Builder - Multi-dimensional indexing
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum


class EvalDimension(str, Enum):
    CORRECTNESS = "correctness"
    EFFICIENCY = "efficiency"
    SAFETY = "safety"
    UX = "ux"


class EvalLevel(str, Enum):
    UNIT = "unit"
    INTEGRATION = "integration"
    SYSTEM = "system"
    E2E = "e2e"


@dataclass
class EvalPackage:
    """Evaluation package metadata"""

    name: str
    version: str
    dimension: EvalDimension
    level: EvalLevel
    description: str
    tags: List[str] = field(default_factory=list)
    entry_point: Optional[str] = None


class IndexBuilder:
    """Index builder for evaluation packages"""

    def __init__(self):
        self._dimension_index: Dict[EvalDimension, List[EvalPackage]] = {
            d: [] for d in EvalDimension
        }
        self._level_index: Dict[EvalLevel, List[EvalPackage]] = {
            l: [] for l in EvalLevel
        }
        self._tag_index: Dict[str, List[EvalPackage]] = {}
        self._name_index: Dict[str, EvalPackage] = {}

    def register_package(self, package: EvalPackage):
        """Register an evaluation package"""
        self._name_index[package.name] = package

        self._dimension_index[package.dimension].append(package)
        self._level_index[package.level].append(package)

        for tag in package.tags:
            if tag not in self._tag_index:
                self._tag_index[tag] = []
            self._tag_index[tag].append(package)

    def build_dimension_index(self, dimension: EvalDimension) -> List[EvalPackage]:
        """Build index by dimension"""
        return self._dimension_index.get(dimension, [])

    def build_level_index(self, level: EvalLevel) -> List[EvalPackage]:
        """Build index by level"""
        return self._level_index.get(level, [])

    def build_feature_index(self, feature_code: str) -> List[EvalPackage]:
        """Build index by feature code"""
        return self._tag_index.get(feature_code, [])

    def search(
        self,
        dimension: Optional[EvalDimension] = None,
        level: Optional[EvalLevel] = None,
        tags: Optional[List[str]] = None,
    ) -> List[EvalPackage]:
        """Multi-dimensional search"""
        results = list(self._name_index.values())

        if dimension:
            results = [p for p in results if p.dimension == dimension]

        if level:
            results = [p for p in results if p.level == level]

        if tags:
            results = [p for p in results if any(t in p.tags for t in tags)]

        return results

    def get_package(self, name: str) -> Optional[EvalPackage]:
        """Get package by name"""
        return self._name_index.get(name)

    def list_all(self) -> List[EvalPackage]:
        """List all packages"""
        return list(self._name_index.values())

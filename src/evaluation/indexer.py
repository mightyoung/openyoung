"""
Evaluation Index Builder - Multi-dimensional indexing
"""

from dataclasses import dataclass, field
from enum import Enum

# 统一数据类型：优先使用 metrics.py 的定义
try:
    from .metrics import EvaluationDimension

    # 导出为通用名称
    EvalDimension = EvaluationDimension
except ImportError:
    # 回退定义
    class EvalDimension(str, Enum):
        CORRECTNESS = "correctness"
        EFFICIENCY = "efficiency"
        SAFETY = "safety"
        UX = "ux"


class EvalLevel(str, Enum):
    """评估层级"""

    UNIT = "unit"
    INTEGRATION = "integration"
    SYSTEM = "system"
    E2E = "e2e"


# 类型别名 - 用于代码清晰度
Dimension = EvalDimension
Level = EvalLevel


@dataclass
class EvalPackage:
    """Evaluation package metadata"""

    name: str
    version: str
    dimension: EvalDimension
    level: EvalLevel
    description: str
    tags: list[str] = field(default_factory=list)
    entry_point: str | None = None


class IndexBuilder:
    """Index builder for evaluation packages"""

    def __init__(self):
        self._dimension_index: dict[EvalDimension, list[EvalPackage]] = {
            d: [] for d in EvalDimension
        }
        self._level_index: dict[EvalLevel, list[EvalPackage]] = {l: [] for l in EvalLevel}
        self._tag_index: dict[str, list[EvalPackage]] = {}
        self._name_index: dict[str, EvalPackage] = {}

    def register_package(self, package: EvalPackage):
        """Register an evaluation package"""
        self._name_index[package.name] = package

        self._dimension_index[package.dimension].append(package)
        self._level_index[package.level].append(package)

        for tag in package.tags:
            if tag not in self._tag_index:
                self._tag_index[tag] = []
            self._tag_index[tag].append(package)

    def build_dimension_index(self, dimension: EvalDimension) -> list[EvalPackage]:
        """Build index by dimension"""
        return self._dimension_index.get(dimension, [])

    def build_level_index(self, level: EvalLevel) -> list[EvalPackage]:
        """Build index by level"""
        return self._level_index.get(level, [])

    def build_feature_index(self, feature_code: str) -> list[EvalPackage]:
        """Build index by feature code"""
        return self._tag_index.get(feature_code, [])

    def search(
        self,
        dimension: EvalDimension | None = None,
        level: EvalLevel | None = None,
        tags: list[str] | None = None,
    ) -> list[EvalPackage]:
        """Multi-dimensional search"""
        results = list(self._name_index.values())

        if dimension:
            results = [p for p in results if p.dimension == dimension]

        if level:
            results = [p for p in results if p.level == level]

        if tags:
            results = [p for p in results if any(t in p.tags for t in tags)]

        return results

    def get_package(self, name: str) -> EvalPackage | None:
        """Get package by name"""
        return self._name_index.get(name)

    def list_all(self) -> list[EvalPackage]:
        """List all packages"""
        return list(self._name_index.values())

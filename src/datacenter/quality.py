"""
Data Quality Scoring System - 数据质量评分系统

提供数据资产的质量评分，包括：
- 完整性评分
- 一致性评分
- 准确性评分
- 可用性评分
- 综合评分

参考数据质量框架:
- DAMA-DMBOK 数据质量维度
- AWS Data Quality metrics
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class QualityDimension(Enum):
    """数据质量维度"""

    COMPLETENESS = "completeness"  # 完整性
    CONSISTENCY = "consistency"  # 一致性
    ACCURACY = "accuracy"  # 准确性
    AVAILABILITY = "availability"  # 可用性
    TIMELINESS = "timeliness"  # 时效性
    UNIQUENESS = "uniqueness"  # 唯一性


@dataclass
class QualityScore:
    """质量评分"""

    dimension: QualityDimension
    score: float  # 0-1
    details: dict[str, Any]
    timestamp: datetime


@dataclass
class DataQualityReport:
    """数据质量报告"""

    # 元数据
    resource_id: str
    resource_type: str  # "run", "step", "execution"
    generated_at: datetime

    # 维度评分
    completeness: float
    consistency: float
    accuracy: float
    availability: float
    timeliness: float
    uniqueness: float

    # 综合评分
    overall_score: float
    grade: str  # "A", "B", "C", "D", "F"

    # 详情
    details: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "resource_id": self.resource_id,
            "resource_type": self.resource_type,
            "generated_at": self.generated_at.isoformat(),
            "dimensions": {
                "completeness": self.completeness,
                "consistency": self.consistency,
                "accuracy": self.accuracy,
                "availability": self.availability,
                "timeliness": self.timeliness,
                "uniqueness": self.uniqueness,
            },
            "overall_score": self.overall_score,
            "grade": self.grade,
            "details": self.details,
        }


class DataQualityScorer:
    """数据质量评分器"""

    def __init__(self):
        pass

    def score_run(self, run_data: dict[str, Any]) -> DataQualityReport:
        """对运行数据评分

        Args:
            run_data: 运行数据字典

        Returns:
            质量报告
        """
        resource_id = run_data.get("run_id", "unknown")
        now = datetime.now()

        # 1. 完整性评分
        completeness = self._score_completeness(run_data)

        # 2. 一致性评分
        consistency = self._score_consistency(run_data)

        # 3. 准确性评分
        accuracy = self._score_accuracy(run_data)

        # 4. 可用性评分
        availability = self._score_availability(run_data)

        # 5. 时效性评分
        timeliness = self._score_timeliness(run_data)

        # 6. 唯一性评分
        uniqueness = self._score_uniqueness(run_data)

        # 计算综合评分
        overall = (
            completeness * 0.2
            + consistency * 0.2
            + accuracy * 0.2
            + availability * 0.15
            + timeliness * 0.1
            + uniqueness * 0.15
        )

        # 评分等级
        grade = self._calculate_grade(overall)

        details = {
            "total_fields": len(run_data),
            "missing_fields": self._count_missing_fields(run_data),
            "has_timestamps": "start_time" in run_data,
            "has_metrics": "metrics" in run_data,
        }

        return DataQualityReport(
            resource_id=resource_id,
            resource_type="run",
            generated_at=now,
            completeness=completeness,
            consistency=consistency,
            accuracy=accuracy,
            availability=availability,
            timeliness=timeliness,
            uniqueness=uniqueness,
            overall_score=overall,
            grade=grade,
            details=details,
        )

    def _score_completeness(self, data: dict[str, Any]) -> float:
        """完整性评分 - 检查必需字段是否存在"""
        required_fields = [
            "run_id",
            "status",
            "start_time",
        ]

        present = sum(1 for f in required_fields if f in data and data[f] is not None)
        return present / len(required_fields)

    def _score_consistency(self, data: dict[str, Any]) -> float:
        """一致性评分 - 检查数据内部一致性"""
        score = 1.0

        # 检查时间一致性
        if "start_time" in data and "end_time" in data:
            try:
                start = data["start_time"]
                end = data["end_time"]
                if isinstance(start, str) and isinstance(end, str):
                    from datetime import datetime

                    s = datetime.fromisoformat(start.replace("Z", "+00:00"))
                    e = datetime.fromisoformat(end.replace("Z", "+00:00"))
                    if e < s:
                        score *= 0.5  # 结束时间早于开始时间
            except:
                score *= 0.8

        # 检查状态有效性
        if "status" in data:
            valid_statuses = ["pending", "running", "completed", "failed", "cancelled"]
            if data["status"] not in valid_statuses:
                score *= 0.7

        return score

    def _score_accuracy(self, data: dict[str, Any]) -> float:
        """准确性评分 - 检查数据值是否合理"""
        score = 1.0

        # 检查 token 计数合理性
        if "prompt_tokens" in data and "completion_tokens" in data:
            pt = data["prompt_tokens"]
            ct = data["completion_tokens"]
            if isinstance(pt, (int, float)) and isinstance(ct, (int, float)):
                if pt < 0 or ct < 0:
                    score *= 0.5
                elif pt > 1000000 or ct > 1000000:  # 异常大值
                    score *= 0.8

        # 检查成本合理性
        if "cost_usd" in data:
            cost = data["cost_usd"]
            if isinstance(cost, (int, float)) and cost < 0:
                score *= 0.5  # 负成本不合理

        return score

    def _score_availability(self, data: dict[str, Any]) -> float:
        """可用性评分 - 检查数据是否可用于分析"""
        score = 1.0

        # 至少有一些数据
        if len(data) < 3:
            score *= 0.5
        elif len(data) < 5:
            score *= 0.8

        # 有错误信息但状态不是失败
        if "error" in data and data.get("status") != "failed":
            score *= 0.7

        return score

    def _score_timeliness(self, data: dict[str, Any]) -> float:
        """时效性评分 - 检查数据是否最新"""
        if "timestamp" not in data and "start_time" not in data:
            return 0.5  # 没有时间戳

        try:
            # 获取最新时间戳
            ts = data.get("timestamp") or data.get("start_time")
            if isinstance(ts, str):
                from datetime import datetime, timedelta

                record_time = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                now = datetime.now(record_time.tzinfo)
                age = (now - record_time).total_seconds()

                # 1小时内为100%, 1天为80%, 1周为60%, 1月为40%
                if age < 3600:
                    return 1.0
                elif age < 86400:
                    return 0.9
                elif age < 604800:
                    return 0.7
                elif age < 2592000:
                    return 0.5
                else:
                    return 0.3
        except:
            pass

        return 0.6  # 默认中等

    def _score_uniqueness(self, data: dict[str, Any]) -> float:
        """唯一性评分 - 检查是否有重复数据"""
        # 简单的唯一性检查：是否有 ID
        if "run_id" in data and data["run_id"]:
            return 1.0
        return 0.5

    def _count_missing_fields(self, data: dict[str, Any]) -> int:
        """计算缺失字段数"""
        return sum(1 for v in data.values() if v is None)

    def _calculate_grade(self, score: float) -> str:
        """根据分数计算等级"""
        if score >= 0.9:
            return "A"
        elif score >= 0.8:
            return "B"
        elif score >= 0.7:
            return "C"
        elif score >= 0.6:
            return "D"
        else:
            return "F"

    def score_batch(self, runs: list[dict[str, Any]]) -> list[DataQualityReport]:
        """批量评分

        Args:
            runs: 运行数据列表

        Returns:
            质量报告列表
        """
        return [self.score_run(run) for run in runs]

    def get_average_scores(self, reports: list[DataQualityReport]) -> dict[str, float]:
        """获取平均分数

        Args:
            reports: 质量报告列表

        Returns:
            各维度平均分
        """
        if not reports:
            return {}

        return {
            "completeness": sum(r.completeness for r in reports) / len(reports),
            "consistency": sum(r.consistency for r in reports) / len(reports),
            "accuracy": sum(r.accuracy for r in reports) / len(reports),
            "availability": sum(r.availability for r in reports) / len(reports),
            "timeliness": sum(r.timeliness for r in reports) / len(reports),
            "uniqueness": sum(r.uniqueness for r in reports) / len(reports),
            "overall": sum(r.overall_score for r in reports) / len(reports),
        }


# ========== Convenience Functions ==========


def create_scorer() -> DataQualityScorer:
    """创建评分器"""
    return DataQualityScorer()


def score_data_resource(resource_data: dict[str, Any]) -> DataQualityReport:
    """便捷函数：对数据资源评分"""
    scorer = DataQualityScorer()
    return scorer.score_run(resource_data)

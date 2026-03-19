"""
DriftDetector - 偏离检测器

M2.2: 检测执行与规划的偏离
"""
from ..types.verification import VerificationStatus, DriftLevel, DriftReport, FeatureStatus
from ..types.document import Priority
from ..types.contract import ExecutionContract


class DriftDetector:
    """偏离检测器

    检测执行与规划的偏离
    """

    def __init__(self, threshold_map: dict = None):
        """初始化检测器

        Args:
            threshold_map: 优先级阈值映射
        """
        self.threshold_map = threshold_map or {
            Priority.MUST: 0,    # must项不允许失败
            Priority.SHOULD: 30,  # should项容忍30%失败
            Priority.COULD: 50    # could项容忍50%失败
        }

    def detect(
        self,
        statuses: list[FeatureStatus],
        contract: ExecutionContract = None
    ) -> DriftReport:
        """检测偏离

        Args:
            statuses: 功能点状态列表
            contract: 执行合约（可选，用于获取优先级信息）

        Returns:
            DriftReport: 偏离报告
        """
        if not statuses:
            return DriftReport(
                drift_score=0,
                level=DriftLevel.NONE,
                verified_count=0,
                failed_count=0,
                total_count=0,
                recommendations=["No features to verify"]
            )

        total = len(statuses)
        verified = sum(1 for s in statuses if s.status == VerificationStatus.VERIFIED)
        failed = sum(1 for s in statuses if s.status == VerificationStatus.FAILED)
        skipped = sum(1 for s in statuses if s.status == VerificationStatus.SKIPPED)

        # 计算偏离度（基于失败率）
        drift_score = (failed / total * 100) if total > 0 else 0

        # 确定严重程度
        level = self._determine_level(drift_score, statuses, contract)

        # 生成建议
        recommendations = self._generate_recommendations(statuses, contract)

        return DriftReport(
            drift_score=drift_score,
            level=level,
            verified_count=verified,
            failed_count=failed,
            total_count=total,
            recommendations=recommendations
        )

    def _determine_level(
        self,
        score: float,
        statuses: list[FeatureStatus],
        contract: ExecutionContract = None
    ) -> DriftLevel:
        """确定偏离级别

        Args:
            score: 偏离分数
            statuses: 功能点状态列表
            contract: 执行合约

        Returns:
            DriftLevel: 偏离级别
        """
        # 检查must级别是否有失败
        if contract:
            must_failed = self._has_priority_failure(statuses, contract, Priority.MUST)
            if must_failed:
                return DriftLevel.CRITICAL

        # 基于分数判断
        if score >= 50:
            return DriftLevel.CRITICAL
        elif score >= 30:
            return DriftLevel.SEVERE
        elif score >= 15:
            return DriftLevel.MODERATE
        elif score >= 5:
            return DriftLevel.MINOR
        return DriftLevel.NONE

    def _has_priority_failure(
        self,
        statuses: list[FeatureStatus],
        contract: ExecutionContract,
        priority: Priority
    ) -> bool:
        """检查是否有指定优先级的失败

        Args:
            statuses: 功能点状态列表
            contract: 执行合约
            priority: 优先级

        Returns:
            bool: 是否有失败
        """
        if not contract:
            return False

        for status in statuses:
            if status.status != VerificationStatus.FAILED:
                continue

            try:
                req = contract.get_requirement(status.req_id)
                if req.priority == priority:
                    return True
            except ValueError:
                continue

        return False

    def _generate_recommendations(
        self,
        statuses: list[FeatureStatus],
        contract: ExecutionContract = None
    ) -> list[str]:
        """生成修正建议

        Args:
            statuses: 功能点状态列表
            contract: 执行合约

        Returns:
            list[str]: 建议列表
        """
        recommendations = []

        failed_must = []
        failed_should = []
        failed_could = []

        for status in statuses:
            if status.status != VerificationStatus.FAILED:
                continue

            if contract:
                try:
                    req = contract.get_requirement(status.req_id)
                    priority = req.priority
                except ValueError:
                    priority = Priority.SHOULD
            else:
                priority = Priority.SHOULD

            if priority == Priority.MUST:
                failed_must.append(status)
            elif priority == Priority.SHOULD:
                failed_should.append(status)
            else:
                failed_could.append(status)

        if failed_must:
            recommendations.append(
                f"【严重】{len(failed_must)}个MUST级别功能点未实现，建议优先修复: "
                f"{[s.req_id for s in failed_must]}"
            )

        if failed_should:
            recommendations.append(
                f"【中等】{len(failed_should)}个SHOULD级别功能点未实现: "
                f"{[s.req_id for s in failed_should]}"
            )

        if failed_could:
            recommendations.append(
                f"【低】{len(failed_could)}个COULD级别功能点未实现（可选项）: "
                f"{[s.req_id for s in failed_could]}"
            )

        if not recommendations:
            recommendations.append("所有功能点均已正确实现，执行与规划对齐良好。")

        return recommendations

    def detect_from_tracker(self, tracker) -> DriftReport:
        """从tracker检测偏离

        Args:
            tracker: FeatureTracker实例

        Returns:
            DriftReport: 偏离报告
        """
        statuses = list(tracker.statuses.values())
        return self.detect(statuses, tracker.contract)


def detect_drift(
    statuses: list[FeatureStatus],
    contract: ExecutionContract = None
) -> DriftReport:
    """检测偏离的便捷函数

    Args:
        statuses: 功能点状态列表
        contract: 执行合约

    Returns:
        DriftReport: 偏离报告
    """
    detector = DriftDetector()
    return detector.detect(statuses, contract)

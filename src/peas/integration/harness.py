"""
PEASHarnessIntegration - PEAS与Harness引擎的集成

M3.1: 与Harness引擎集成

集成流程:
1. 解析用户Markdown规格文档
2. 构建执行合约
3. 配置HarnessEngine执行器
4. 执行任务并验证
5. 检测偏离并报告
"""
from typing import Any, Optional, AsyncGenerator, Callable
import logging

from src.agents.harness.engine import HarnessEngine, HarnessConfig
from src.agents.harness.types import ExecutionPhase
from src.peas.understanding.markdown_parser import MarkdownParser
from src.peas.contract.builder import ContractBuilder
from src.peas.verification.tracker import FeatureTracker
from src.peas.verification.drift_detector import DriftDetector
from src.peas.learning.preference_learner import PreferenceLearner
from src.peas.types import (
    ParsedDocument,
    ExecutionContract,
    FeatureStatus,
    DriftReport,
    Priority,
)

logger = logging.getLogger(__name__)


class PEASHarnessIntegration:
    """PEAS与HarnessEngine的集成类

    负责:
    - 解析Markdown规格文档
    - 构建执行合约
    - 配置HarnessEngine执行器
    - 验证执行结果
    - 检测并报告偏离
    """

    def __init__(
        self,
        llm_client: Optional[Any] = None,
        harness_config: Optional[HarnessConfig] = None,
        preference_learner: Optional[PreferenceLearner] = None,
    ):
        """初始化集成

        Args:
            llm_client: LLM客户端（用于LLM验证）
            harness_config: Harness配置
            preference_learner: 用户偏好学习器（可选）
        """
        self.llm = llm_client
        self.harness_config = harness_config or HarnessConfig()

        # PEAS组件
        self._parser = MarkdownParser()
        self._contract_builder = ContractBuilder(llm_client)
        self._tracker: Optional[FeatureTracker] = None
        self._drift_detector = DriftDetector()
        self._preference_learner = preference_learner or PreferenceLearner()

        # 解析结果
        self._parsed_doc: Optional[ParsedDocument] = None
        self._contract: Optional[ExecutionContract] = None

        # HarnessEngine
        self._engine: Optional[HarnessEngine] = None

    def parse_spec(self, spec_content: str) -> ParsedDocument:
        """解析Markdown规格文档

        Args:
            spec_content: Markdown格式的规格文档内容

        Returns:
            ParsedDocument: 结构化的文档对象
        """
        self._parsed_doc = self._parser.parse(spec_content)
        logger.info(
            f"Parsed spec: {self._parsed_doc.title}, "
            f"{self._parsed_doc.total_features} features"
        )
        return self._parsed_doc

    def parse_spec_file(self, file_path: str) -> ParsedDocument:
        """从文件解析Markdown规格文档

        Args:
            file_path: Markdown文件路径

        Returns:
            ParsedDocument: 结构化的文档对象
        """
        self._parsed_doc = self._parser.parse_file(file_path)
        logger.info(
            f"Parsed spec file: {self._parsed_doc.title}, "
            f"{self._parsed_doc.total_features} features"
        )
        return self._parsed_doc

    def build_contract(self) -> ExecutionContract:
        """从解析的文档构建执行合约

        Returns:
            ExecutionContract: 可执行的合约

        Raises:
            RuntimeError: 如果尚未解析文档
        """
        if not self._parsed_doc:
            raise RuntimeError("Must parse spec before building contract")

        self._contract = self._contract_builder.build(self._parsed_doc)
        self._tracker = FeatureTracker(self._contract, self.llm)
        logger.info(
            f"Built contract: {self._contract.contract_id[:8]}, "
            f"{self._contract.total_requirements} requirements"
        )
        return self._contract

    async def execute(
        self,
        task_description: str,
        executor_fn: Optional[Callable] = None,
        context: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """执行任务并验证

        Args:
            task_description: 任务描述
            executor_fn: 自定义执行器函数
            context: 额外上下文

        Returns:
            dict: 包含执行结果、验证状态和偏离报告
        """
        if not self._contract:
            raise RuntimeError("Must build contract before execution")

        # 创建HarnessEngine
        self._engine = HarnessEngine(self.harness_config)

        # 设置执行器
        executor = executor_fn or self._create_executor()
        self._engine.set_executor(executor)

        # 设置评估器
        self._engine.set_evaluator(self._create_evaluator())

        # 执行
        context = context or {}
        context["contract_id"] = self._contract.contract_id

        result = await self._engine.execute(task_description, context)

        # 验证结果
        execution_text = str(result.get("result", ""))
        feature_statuses = await self._tracker.verify(execution_text)

        # 记录验证结果到偏好学习器（用于后续用户反馈学习）
        await self._record_verification_for_learning(feature_statuses, execution_text)

        # 获取调整后的阈值
        adjusted_thresholds = await self._get_adjusted_thresholds()

        # 使用调整后的阈值检测偏离
        drift_report = self._drift_detector.detect(feature_statuses, self._contract)

        return {
            "execution_result": result,
            "feature_statuses": feature_statuses,
            "drift_report": drift_report,
            "alignment_rate": drift_report.alignment_rate,
            "adjusted_thresholds": adjusted_thresholds,
        }

    async def _record_verification_for_learning(
        self,
        feature_statuses: list,
        execution_text: str,
    ) -> None:
        """记录验证结果用于学习

        Args:
            feature_statuses: 功能点状态列表
            execution_text: 执行结果文本
        """
        # 学习输出风格偏好
        await self._preference_learner.learn_style_preference(execution_text)

        # 记录每个功能点的验证状态
        for status in feature_statuses:
            # 获取该功能点的优先级
            priority = Priority.SHOULD
            if self._contract:
                try:
                    req = self._contract.get_requirement(status.req_id)
                    priority = req.priority
                except ValueError:
                    pass

            # 记录到偏好学习器（假设验证通过的状态为"接受"）
            await self._preference_learner.record_feedback(
                feature_id=status.req_id,
                accepted=status.is_verified(),
                context={
                    "priority": priority,
                    "status": status.status.value,
                },
            )

            # 记录结果模式
            self._preference_learner.record_result_pattern(
                result=str(status.evidence) if status.evidence else "",
                accepted=status.is_verified(),
                verification_status=status.status,
            )

    async def _get_adjusted_thresholds(self) -> dict[str, float]:
        """获取调整后的阈值

        Returns:
            dict: 优先级到调整后阈值的映射
        """
        thresholds = {}
        for priority in Priority:
            # 为每个优先级获取一个代表性的调整阈值
            feature_id = f"_priority_{priority.value}"
            threshold = await self._preference_learner.get_adjusted_threshold(feature_id)
            thresholds[priority.value] = threshold
        return thresholds

    async def record_user_feedback(
        self,
        feature_id: str,
        accepted: bool,
        context: Optional[dict] = None,
    ) -> None:
        """记录用户反馈

        Args:
            feature_id: 功能点ID
            accepted: 用户是否接受验证结果
            context: 额外上下文
        """
        await self._preference_learner.record_feedback(feature_id, accepted, context)

    def get_preference_stats(self) -> dict:
        """获取偏好学习统计

        Returns:
            dict: 偏好统计信息
        """
        return {
            "thresholds": self._preference_learner.get_current_thresholds(),
            "acceptance": self._preference_learner.get_acceptance_stats(),
            "patterns": self._preference_learner.get_learned_patterns(),
        }

    async def execute_streaming(
        self,
        task_description: str,
        executor_fn: Optional[Callable] = None,
        context: Optional[dict[str, Any]] = None,
    ) -> AsyncGenerator[dict, None]:
        """流式执行任务

        Args:
            task_description: 任务描述
            executor_fn: 自定义执行器函数
            context: 额外上下文

        Yields:
            dict: 每个阶段的执行结果
        """
        if not self._contract:
            raise RuntimeError("Must build contract before execution")

        self._engine = HarnessEngine(self.harness_config)
        executor = executor_fn or self._create_executor()
        self._engine.set_executor(executor)
        self._engine.set_evaluator(self._create_evaluator())

        context = context or {}
        context["contract_id"] = self._contract.contract_id

        async for exec_result in self._engine.execute_streaming(task_description, context):
            yield {
                "phase": exec_result.phase.value,
                "iteration": exec_result.iteration,
                "status": exec_result.status.value,
                "result": exec_result.result,
                "evaluation": exec_result.evaluation.value if exec_result.evaluation else None,
                "feedback_action": (
                    exec_result.feedback_action.value if exec_result.feedback_action else None
                ),
                "error": exec_result.error,
                "duration": exec_result.duration,
            }

    def _create_executor(self):
        """创建Harness执行器回调"""
        async def executor(task_description: str, context: dict) -> str:
            raise NotImplementedError(
                "Subclass must implement executor or provide custom executor"
            )

        return executor

    def _create_evaluator(self):
        """创建Harness评估器回调"""
        async def evaluator(result: Any, phase: ExecutionPhase, context: dict) -> bool:
            if not self._tracker:
                return True

            result_text = str(result) if result else ""
            statuses = await self._tracker.verify(result_text)

            for status in statuses:
                if status.is_failed():
                    req = self._contract.get_requirement(status.req_id)
                    if req.priority.value == "must":
                        return False

            return True

        return evaluator

    def get_drift_report(self) -> Optional[DriftReport]:
        """获取当前偏离报告"""
        if not self._tracker:
            return None
        return self._drift_detector.detect_from_tracker(self._tracker)

    def get_feature_summary(self) -> dict:
        """获取功能点验证摘要"""
        if not self._tracker:
            return {}
        return self._tracker.get_summary()


def create_integration(
    llm_client: Optional[Any] = None,
) -> PEASHarnessIntegration:
    """创建PEAS集成的便捷函数

    Args:
        llm_client: LLM客户端

    Returns:
        PEASHarnessIntegration: 集成实例
    """
    return PEASHarnessIntegration(llm_client=llm_client)

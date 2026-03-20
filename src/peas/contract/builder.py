"""
ContractBuilder - 构建可执行合约

M1.3: 构建ExecutionContract
"""

import uuid
from datetime import datetime
from typing import Optional

from ..types.contract import ContractRequirement, ExecutionContract, IntentSpec
from ..types.document import FeaturePoint, ParsedDocument, Priority
from ..types.verification import VerificationStatus


class ContractBuilder:
    """合约构建器

    从ParsedDocument和IntentSpec构建ExecutionContract
    """

    def __init__(self, llm_client=None):
        """初始化合约构建器

        Args:
            llm_client: 可选的LLM客户端，用于生成验证prompt
        """
        self.llm = llm_client

    def build(self, doc: ParsedDocument, intent: Optional[IntentSpec] = None) -> ExecutionContract:
        """构建执行合约

        Args:
            doc: 解析后的文档
            intent: 意图规格

        Returns:
            ExecutionContract: 可执行的合约
        """
        requirements = []

        for fp in doc.feature_points:
            req = self._create_requirement(fp)
            requirements.append(req)

        return ExecutionContract.create(
            requirements=requirements,
            intent=intent,
            version="1.0",
            metadata={
                "title": doc.title,
                "total_features": len(doc.feature_points),
                "must_count": len(doc.must_features),
                "should_count": len(doc.should_features),
            },
        )

    def _create_requirement(self, fp: FeaturePoint) -> ContractRequirement:
        """从功能点创建需求

        Args:
            fp: 功能点

        Returns:
            ContractRequirement: 合约需求
        """
        verification_method = self._determine_verification_method(fp)
        verification_prompt = self._generate_verification_prompt(fp)

        return ContractRequirement(
            req_id=fp.id,
            description=fp.title,
            priority=fp.priority,
            verification_method=verification_method,
            verification_prompt=verification_prompt,
            metadata={
                "section": fp.related_section,
                "acceptance_criteria": fp.acceptance_criteria,
            },
        )

    def _determine_verification_method(self, fp: FeaturePoint) -> str:
        """确定验证方法

        Args:
            fp: 功能点

        Returns:
            str: 验证方法 ("llm_judge" | "regex" | "manual")
        """
        if fp.acceptance_criteria:
            return "llm_judge"
        elif fp.priority == Priority.MUST:
            return "llm_judge"
        else:
            return "regex"

    def _generate_verification_prompt(self, fp: FeaturePoint) -> str:
        """生成验证prompt

        Args:
            fp: 功能点

        Returns:
            str: 验证prompt
        """
        if fp.acceptance_criteria:
            criteria_text = "\n".join(f"- {c}" for c in fp.acceptance_criteria)
            return f"""验证功能点是否正确实现：

功能点: {fp.title}
优先级: {fp.priority.value}

验收标准:
{criteria_text}

请判断实现是否满足上述验收标准，并给出简短理由。"""

        return f"""验证功能点是否正确实现：

功能点: {fp.title}
优先级: {fp.priority.value}

请判断实现是否满足该功能点的需求，并给出简短理由。"""


def build_contract(doc: ParsedDocument, intent: Optional[IntentSpec] = None) -> ExecutionContract:
    """构建合约的便捷函数

    Args:
        doc: 解析后的文档
        intent: 意图规格

    Returns:
        ExecutionContract: 可执行的合约
    """
    builder = ContractBuilder()
    return builder.build(doc, intent)

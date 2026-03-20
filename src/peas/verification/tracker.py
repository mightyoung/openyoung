"""
FeatureTracker - 功能点追踪器

M2.1: 追踪功能点执行状态
"""

import re
from typing import Optional

from ..types.contract import ContractRequirement, ExecutionContract
from ..types.document import Priority
from ..types.verification import FeatureStatus, VerificationStatus


class FeatureTracker:
    """功能点追踪器

    追踪功能点的验证状态
    """

    def __init__(self, contract: ExecutionContract, llm_client=None):
        """初始化追踪器

        Args:
            contract: 执行合约
            llm_client: 可选的LLM客户端
        """
        self.contract = contract
        self.llm = llm_client
        self.statuses: dict[str, FeatureStatus] = {}

    async def verify(self, execution_result: str) -> list[FeatureStatus]:
        """验证执行结果

        Args:
            execution_result: 执行结果文本

        Returns:
            list[FeatureStatus]: 功能点状态列表
        """
        results = []

        for req in self.contract.requirements:
            if req.verification_method == "llm_judge":
                result = await self._llm_verify(req, execution_result)
            else:
                result = await self._regex_verify(req, execution_result)

            results.append(result)
            self.statuses[req.req_id] = result

        return results

    def verify_sync(self, execution_result: str) -> list[FeatureStatus]:
        """同步验证执行结果（不使用LLM）

        Args:
            execution_result: 执行结果文本

        Returns:
            list[FeatureStatus]: 功能点状态列表
        """
        results = []

        for req in self.contract.requirements:
            result = self._regex_verify(req, execution_result)
            results.append(result)
            self.statuses[req.req_id] = result

        return results

    async def _llm_verify(self, req: ContractRequirement, execution: str) -> FeatureStatus:
        """LLM验证

        Args:
            req: 合约需求
            execution: 执行结果

        Returns:
            FeatureStatus: 功能点状态
        """
        if not self.llm:
            # 如果没有LLM客户端，降级到正则验证
            return self._regex_verify(req, execution)

        prompt = f"""验证以下需求是否被正确实现：

需求: {req.description}
优先级: {req.priority.value}
验收标准: {req.verification_prompt or "无"}

执行结果:
{execution}

请判断实现是否满足需求。回答格式：
- 如果满足: PASS - 简短理由
- 如果不满足: FAIL - 简短理由
"""

        response = await self.llm.generate(prompt)
        passed = self._parse_verdict(response)

        return FeatureStatus(
            req_id=req.req_id,
            status=VerificationStatus.VERIFIED if passed else VerificationStatus.FAILED,
            evidence=[response],
            notes=req.description,
        )

    def _regex_verify(self, req: ContractRequirement, execution: str) -> FeatureStatus:
        """正则验证

        Args:
            req: 合约需求
            execution: 执行结果

        Returns:
            FeatureStatus: 功能点状态
        """
        # 简单的关键词匹配验证
        description = req.description.lower()
        execution_lower = execution.lower()

        # 提取关键词（取标题中的主要词汇）
        keywords = [w for w in description.split() if len(w) > 2]

        if not keywords:
            # 没有关键词，无法验证
            return FeatureStatus(
                req_id=req.req_id,
                status=VerificationStatus.SKIPPED,
                evidence=["No keywords to verify"],
                notes=req.description,
            )

        # 检查关键词是否出现在执行结果中
        matched_keywords = [k for k in keywords if k in execution_lower]
        match_rate = len(matched_keywords) / len(keywords) if keywords else 0

        if match_rate >= 0.5:
            return FeatureStatus(
                req_id=req.req_id,
                status=VerificationStatus.VERIFIED,
                evidence=[f"Matched keywords: {matched_keywords}"],
                notes=req.description,
            )
        else:
            return FeatureStatus(
                req_id=req.req_id,
                status=VerificationStatus.FAILED,
                evidence=[
                    f"Match rate: {match_rate:.0%}, missing: {[k for k in keywords if k not in matched_keywords]}"
                ],
                notes=req.description,
            )

    def _parse_verdict(self, response: str) -> bool:
        """解析LLM判决

        Args:
            response: LLM响应

        Returns:
            bool: 是否通过
        """
        response_lower = response.lower().strip()

        # 简单匹配
        if response_lower.startswith("pass"):
            return True
        elif response_lower.startswith("fail"):
            return False

        # 检查关键词
        if any(word in response_lower for word in ["通过", "满足", "正确", "成功", "符合"]):
            return True
        elif any(word in response_lower for word in ["不通过", "不满足", "失败", "错误", "不符合"]):
            return False

        # 默认失败
        return False

    def get_status(self, req_id: str) -> FeatureStatus:
        """获取指定功能点状态

        Args:
            req_id: 功能点ID

        Returns:
            FeatureStatus: 功能点状态
        """
        return self.statuses.get(req_id)

    def get_summary(self) -> dict:
        """获取验证摘要

        Returns:
            dict: 验证摘要
        """
        total = len(self.statuses)
        verified = sum(1 for s in self.statuses.values() if s.status == VerificationStatus.VERIFIED)
        failed = sum(1 for s in self.statuses.values() if s.status == VerificationStatus.FAILED)
        skipped = sum(1 for s in self.statuses.values() if s.status == VerificationStatus.SKIPPED)

        return {
            "total": total,
            "verified": verified,
            "failed": failed,
            "skipped": skipped,
            "pass_rate": verified / total if total > 0 else 0,
        }

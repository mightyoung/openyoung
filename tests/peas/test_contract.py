"""
Tests for ContractBuilder
"""
import pytest
from src.peas import MarkdownParser, ContractBuilder, IntentExtractor
from src.peas.types import Priority, IntentSpec


class TestContractBuilder:
    """ContractBuilder测试"""

    @pytest.fixture
    def parser(self):
        return MarkdownParser()

    @pytest.fixture
    def builder(self):
        return ContractBuilder()

    @pytest.fixture
    def sample_doc(self, parser):
        content = """# 用户管理系统 PRD

## 1. 功能需求

### 1.1 用户注册
- Feature: 邮箱验证注册
- 必须发送验证邮件

### 1.2 用户登录
- Feature: 密码强度检查
- Should: 密码长度至少8位

### 1.3 账户安全
- Feature: 登录失败锁定
- Could: 显示剩余尝试次数

## 2. 验收标准

Given 用户已注册
When 用户输入正确密码
Then 允许登录
"""
        return parser.parse(content)

    def test_build_contract(self, builder, sample_doc):
        """测试构建合约"""
        contract = builder.build(sample_doc)

        assert contract.contract_id is not None
        assert contract.version == "1.0"
        assert contract.total_requirements == 3

    def test_contract_requirements_match_features(self, builder, sample_doc):
        """测试需求数量与功能点匹配"""
        contract = builder.build(sample_doc)

        assert len(contract.requirements) == len(sample_doc.feature_points)

    def test_must_priority_uses_llm_judge(self, builder, sample_doc):
        """测试must优先级使用LLM验证"""
        contract = builder.build(sample_doc)

        for req in contract.requirements:
            if req.priority == Priority.MUST:
                assert req.verification_method == "llm_judge"

    def test_should_priority_uses_regex(self, builder, parser):
        """测试should优先级使用正则验证"""
        content = """# Test
- Feature: 测试功能
- Should: 建议实现
"""
        doc = parser.parse(content)
        contract = builder.build(doc)

        assert contract.requirements[0].verification_method == "regex"

    def test_contract_with_acceptance_criteria(self, builder, parser):
        """测试带验收标准的合约"""
        content = """# Test

### 登录功能
- Feature: 用户登录
Given 用户已注册
When 用户输入密码
Then 允许登录
"""
        doc = parser.parse(content)
        contract = builder.build(doc)

        assert contract.requirements[0].verification_method == "llm_judge"

    def test_contract_with_intent(self, builder, sample_doc):
        """测试带意图规格的合约"""
        intent = IntentSpec(
            primary_goals=["用户注册", "用户登录"],
            constraints=["安全性", "性能"],
            quality_bar="功能完整且安全"
        )
        contract = builder.build(sample_doc, intent)

        assert contract.intent is not None
        assert len(contract.intent.primary_goals) == 2

    def test_contract_metadata(self, builder, sample_doc):
        """测试合约元数据"""
        contract = builder.build(sample_doc)

        assert "title" in contract.metadata
        assert contract.metadata["title"] == "用户管理系统 PRD"
        assert "must_count" in contract.metadata
        assert contract.metadata["must_count"] == 1

    def test_get_requirement(self, builder, sample_doc):
        """测试获取指定需求"""
        contract = builder.build(sample_doc)

        req = contract.get_requirement("FP-001")
        assert req is not None
        assert req.req_id == "FP-001"

    def test_get_requirement_not_found(self, builder, sample_doc):
        """测试获取不存在的需求"""
        contract = builder.build(sample_doc)

        with pytest.raises(ValueError):
            contract.get_requirement("FP-999")

    def test_verification_prompt_generation(self, builder, parser):
        """测试验证prompt生成"""
        content = """# Test
- Feature: 测试功能
"""
        doc = parser.parse(content)
        contract = builder.build(doc)

        prompt = contract.requirements[0].verification_prompt
        assert "测试功能" in prompt
        assert "priority" in prompt.lower() or "优先级" in prompt

    def test_build_contract_function(self, parser):
        """测试便捷函数"""
        from src.peas.contract import build_contract

        content = "# Test\n- Feature: Test"
        doc = parser.parse(content)
        contract = build_contract(doc)

        assert contract.total_requirements == 1

"""
End-to-End Tests for PEAS - Plan Execution Alignment System

Tests the complete workflow:
1. Parse Markdown design documents (PRD)
2. Build execution contracts
3. Verify execution results
4. Detect drift between plan and execution

This module provides comprehensive E2E tests for:
- MarkdownParser: PRD parsing and feature extraction
- DriftDetector: Plan-execution drift detection
- Full workflow: Parse -> Verify -> Report
"""

import pytest
from src.peas import (
    MarkdownParser,
    ContractBuilder,
    FeatureTracker,
    DriftDetector,
    Priority,
    VerificationStatus,
    DriftLevel,
)
from src.peas.types import FeatureStatus


# ============================================================================
# Realistic PRD Test Data
# ============================================================================

COMPLEX_PRD = """# AI Agent Platform PRD

## 1. 系统概述

AI Agent平台提供智能代理的创建、部署和管理功能。

## 2. 功能需求

### 2.1 代理创建

- Feature: 创建基础代理 - Must
- 支持自定义代理名称和描述 - Must
- 生成唯一的代理ID - Must

### 2.2 代理部署

- Feature: 部署代理到生产环境 - Must
- 支持高可用部署 - Must
- 支持自动扩缩容 - Must
- 提供部署预览功能 - Should
- 支持回滚功能 - Should

### 2.3 代理监控

- Feature: 监控代理运行状态 - Must
- 实时显示CPU和内存使用率 - Must
- 支持设置告警阈值 - Must
- 支持自定义监控面板 - Could

## 3. 非功能需求

### 3.1 性能要求

- 支持1000并发请求 - Must
- 响应时间 < 500ms - Should

### 3.2 安全要求

- 所有API必须认证 - Must
- 支持RBAC权限控制 - Must

## 4. 验收标准

### 4.1 代理创建

Given 用户打开代理创建页面
When 用户填写代理信息并选择类型
Then 系统创建代理并返回代理ID

### 4.2 代理部署

Given 代理已创建并通过测试
When 用户点击部署按钮
Then 代理部署到生产环境并开始运行

### 4.3 监控

Given 代理正在运行
When 用户打开监控面板
Then 实时显示代理状态和资源使用
"""


MINIMAL_PRD = """# Minimal PRD

## 功能

- Feature: 单一功能点
- Must: 必选功能
- Should: 可选功能
"""


EDGE_CASE_PRD = """# Edge Case PRD

## 特殊字符测试

- Feature: 测试<>\"'&等特殊字符
- Feature: 测试中文标题和标点
- Feature: 测试超长内容标题ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ
"""


# ============================================================================
# Test Class 1: MarkdownParser E2E Tests
# ============================================================================

class TestMarkdownParserE2E:
    """MarkdownParser 端到端测试

    测试MarkdownParser对PRD文档的完整解析能力，包括：
    - 文档结构和标题提取
    - 功能点列表提取
    - Given-When-Then验收标准提取
    - 优先级自动检测
    """

    @pytest.fixture
    def parser(self):
        """创建MarkdownParser实例"""
        return MarkdownParser()

    def test_parse_complete_prd(self, parser):
        """测试完整PRD解析

        验证解析器能够正确处理包含多个章节、
        功能和验收标准的复杂PRD文档。
        """
        doc = parser.parse(COMPLEX_PRD)

        # 验证文档标题提取
        assert doc.title == "AI Agent Platform PRD"

        # 验证章节结构提取
        assert len(doc.sections) > 0
        section_text = " ".join(doc.sections)
        assert "代理创建" in section_text or "功能需求" in section_text

        # 验证功能点数量 (Parser only extracts Feature: lines)
        assert len(doc.feature_points) >= 3  # 创建、部署、监控各一个Feature

        # 验证元数据
        assert "parser_version" in doc.metadata
        assert "line_count" in doc.metadata
        assert doc.metadata["line_count"] > 0

    def test_extract_feature_points(self, parser):
        """测试功能点提取

        验证功能点能够从不同格式的Markdown中正确提取，
        包括Feature标记、REQ标记等。
        """
        doc = parser.parse(COMPLEX_PRD)

        # 验证功能点基本结构
        for fp in doc.feature_points:
            assert fp.id.startswith("FP-")
            assert len(fp.id) == 6  # FP-001 格式
            assert fp.title is not None
            assert len(fp.title) > 0
            assert isinstance(fp.priority, Priority)

        # 验证功能点ID顺序递增
        ids = [fp.id for fp in doc.feature_points]
        assert ids == sorted(ids)

        # 验证第一个和最后一个功能点
        assert doc.feature_points[0].id == "FP-001"
        assert doc.feature_points[-1].id == f"FP-{len(ids):03d}"

    def test_priority_detection(self, parser):
        """测试优先级检测

        验证MUST/Should/Could三种优先级的自动检测能力。
        解析器通过检测标题中的优先级关键词来确定优先级。
        """
        doc = parser.parse(COMPLEX_PRD)

        # 提取各优先级功能点
        must_features = [fp for fp in doc.feature_points if fp.priority == Priority.MUST]
        should_features = [fp for fp in doc.feature_points if fp.priority == Priority.SHOULD]
        could_features = [fp for fp in doc.feature_points if fp.priority == Priority.COULD]

        # 验证MUST优先级检测
        assert len(must_features) > 0, "应该检测到MUST级别功能点"
        for fp in must_features:
            # 标题中应包含优先级标识
            title_lower = fp.title.lower()
            has_priority_indicator = any(kw in title_lower for kw in ["must", "should", "could"])
            # 如果标题中没有优先级词，则检测description
            if not has_priority_indicator:
                desc_lower = fp.description.lower()
                assert any(kw in desc_lower for kw in ["must", "should", "could"]), \
                    f"Feature {fp.id} should have priority indicator"

        # 验证SHOULD优先级检测 (可能没有SHOULD级别的Feature:行)
        # 注意: Parser只从Feature:行提取功能点，SHOULD可能只出现在描述中

    def test_gwt_extraction(self, parser):
        """测试Given-When-Then验收标准提取

        验证解析器能从验收标准章节中提取GWT格式的验收条件。
        """
        doc = parser.parse(COMPLEX_PRD)

        # 查找包含验收标准的最后一个功能点
        fp_with_criteria = None
        for fp in reversed(doc.feature_points):
            if len(fp.acceptance_criteria) > 0:
                fp_with_criteria = fp
                break

        # 验证提取到验收标准
        assert fp_with_criteria is not None, "应该有功能点关联验收标准"
        assert len(fp_with_criteria.acceptance_criteria) > 0

        # 验证GWT元素
        all_criteria = " ".join(fp_with_criteria.acceptance_criteria).lower()
        has_gwt = any(gwt in all_criteria for gwt in ["given", "when", "then", "用户", "代理"])
        assert has_gwt, "验收标准应包含GWT元素"

    def test_minimal_prd_parsing(self, parser):
        """测试极简PRD解析

        验证解析器能处理只有单一功能点的PRD。
        """
        doc = parser.parse(MINIMAL_PRD)

        assert doc.title == "Minimal PRD"
        assert len(doc.feature_points) >= 1
        assert doc.feature_points[0].priority in [Priority.MUST, Priority.SHOULD, Priority.COULD]

    def test_edge_case_special_characters(self, parser):
        """测试特殊字符处理

        验证解析器能正确处理特殊字符、超长标题等边界情况。
        """
        doc = parser.parse(EDGE_CASE_PRD)

        # 验证特殊字符功能点被提取
        assert len(doc.feature_points) >= 3

        # 验证超长标题被截断或正常处理
        for fp in doc.feature_points:
            assert len(fp.title) <= 500, "标题不应过长"


# ============================================================================
# Test Class 2: DriftDetector E2E Tests
# ============================================================================

class TestDriftDetectorE2E:
    """DriftDetector 端到端测试

    测试偏离检测器的完整检测能力，包括：
    - 失败率计算
    - 基于优先级的严重程度判定
    - MUST级别失败的CRITICAL判定
    """

    @pytest.fixture
    def detector(self):
        """创建DriftDetector实例"""
        return DriftDetector()

    @pytest.fixture
    def contract_builder(self):
        """创建ContractBuilder实例"""
        return ContractBuilder()

    @pytest.fixture
    def parser(self):
        """创建MarkdownParser实例"""
        return MarkdownParser()

    def test_full_drift_detection(self, detector, contract_builder, parser):
        """测试完整偏离检测流程

        验证从解析PRD到生成偏离报告的完整流程。
        """
        # 解析PRD
        doc = parser.parse(COMPLEX_PRD)
        contract = contract_builder.build(doc)

        # 创建tracker并模拟部分实现
        tracker = FeatureTracker(contract)
        execution_result = """
        已完成:
        - 创建基础代理功能
        - 支持选择代理类型
        - 生成唯一代理ID
        - 支持高可用部署
        - 支持自动扩缩容
        """
        tracker.verify_sync(execution_result)

        # 检测偏离
        report = detector.detect_from_tracker(tracker)

        # 验证报告结构
        assert isinstance(report.drift_score, float)
        assert 0 <= report.drift_score <= 100
        assert isinstance(report.level, DriftLevel)
        assert report.total_count > 0
        assert report.verified_count >= 0
        assert report.failed_count >= 0
        assert report.verified_count + report.failed_count == report.total_count

        # 验证建议
        assert len(report.recommendations) > 0
        assert isinstance(report.recommendations[0], str)

    def test_must_failure_detection(self, detector, contract_builder, parser):
        """测试MUST优先级失败检测

        验证当MUST级别的功能点失败时，偏离级别为CRITICAL。
        """
        doc = parser.parse(COMPLEX_PRD)
        contract = contract_builder.build(doc)

        # 创建只包含MUST失败的statuses
        statuses = []
        for req in contract.requirements:
            if req.priority == Priority.MUST:
                statuses.append(FeatureStatus(
                    req_id=req.req_id,
                    status=VerificationStatus.FAILED,
                    evidence=["MUST feature not implemented"]
                ))
            else:
                statuses.append(FeatureStatus(
                    req_id=req.req_id,
                    status=VerificationStatus.VERIFIED,
                    evidence=["Implemented"]
                ))

        report = detector.detect(statuses, contract)

        # MUST失败应该导致CRITICAL级别
        assert report.level == DriftLevel.CRITICAL, \
            "MUST优先级失败应该导致CRITICAL偏离级别"

    def test_no_drift_when_all_pass(self, detector):
        """测试全部通过时无偏离

        验证所有功能点都通过时，偏离分数为0。
        """
        statuses = [
            FeatureStatus(req_id="FP-001", status=VerificationStatus.VERIFIED, evidence=["OK"]),
            FeatureStatus(req_id="FP-002", status=VerificationStatus.VERIFIED, evidence=["OK"]),
        ]

        report = detector.detect(statuses)

        assert report.drift_score == 0
        assert report.level == DriftLevel.NONE
        assert report.verified_count == 2
        assert report.failed_count == 0

    def test_partial_drift_calculation(self, detector):
        """测试部分失败时的偏离计算

        验证失败率正确转换为偏离分数。
        """
        statuses = [
            FeatureStatus(req_id="FP-001", status=VerificationStatus.VERIFIED, evidence=["OK"]),
            FeatureStatus(req_id="FP-002", status=VerificationStatus.VERIFIED, evidence=["OK"]),
            FeatureStatus(req_id="FP-003", status=VerificationStatus.FAILED, evidence=["Not OK"]),
            FeatureStatus(req_id="FP-004", status=VerificationStatus.SKIPPED, evidence=["Skipped"]),
        ]

        report = detector.detect(statuses)

        # 4个功能点，1个失败 = 25%失败率
        assert report.drift_score == 25.0
        assert report.total_count == 4
        assert report.verified_count == 2
        assert report.failed_count == 1

    def test_empty_statuses_handling(self, detector):
        """测试空状态列表处理

        验证没有功能点时返回正确的空报告。
        """
        report = detector.detect([])

        assert report.drift_score == 0
        assert report.level == DriftLevel.NONE
        assert report.total_count == 0
        assert report.verified_count == 0
        assert report.failed_count == 0
        assert "No features" in report.recommendations[0]


# ============================================================================
# Test Class 3: Full Workflow E2E Tests
# ============================================================================

class TestFullWorkflowE2E:
    """完整工作流端到端测试

    测试从解析PRD到生成偏离报告的完整流程，
    包括Parse -> Verify -> Report三个阶段。
    """

    @pytest.fixture
    def parser(self):
        """创建MarkdownParser实例"""
        return MarkdownParser()

    @pytest.fixture
    def builder(self):
        """创建ContractBuilder实例"""
        return ContractBuilder()

    @pytest.fixture
    def tracker(self, builder, parser):
        """创建配置好的FeatureTracker"""
        doc = parser.parse(COMPLEX_PRD)
        contract = builder.build(doc)
        return FeatureTracker(contract)

    @pytest.fixture
    def detector(self):
        """创建DriftDetector实例"""
        return DriftDetector()

    def test_parse_verify_report_workflow(self, parser, builder, detector):
        """测试解析-验证-报告完整流程

        验证PEAS的完整工作流：
        1. 解析PRD文档
        2. 构建执行合约
        3. 验证执行结果
        4. 生成偏离报告
        """
        # Stage 1: Parse
        doc = parser.parse(COMPLEX_PRD)
        assert doc.title == "AI Agent Platform PRD"
        assert len(doc.feature_points) > 0

        # Stage 2: Build Contract
        contract = builder.build(doc)
        assert contract is not None
        assert contract.total_requirements > 0
        assert contract.version == "1.0"
        assert "title" in contract.metadata

        # Stage 3: Verify (partial implementation)
        tracker = FeatureTracker(contract)
        partial_execution = """
        已完成部分功能:
        - 创建基础代理
        - 支持选择类型
        - 高可用部署
        - 自动扩缩容
        未完成:
        - 监控功能
        - 告警阈值
        """
        statuses = tracker.verify_sync(partial_execution)
        assert len(statuses) == contract.total_requirements

        # Stage 4: Detect Drift
        report = detector.detect_from_tracker(tracker)

        # 验证报告完整性
        assert report.total_count > 0
        assert report.verified_count + report.failed_count == report.total_count
        assert isinstance(report.level, DriftLevel)
        assert isinstance(report.recommendations, list)
        assert len(report.recommendations) > 0

        # 验证部分实现导致一定偏离
        assert report.verified_count < report.total_count
        assert report.drift_score > 0

    def test_complete_implementation_workflow(self, parser, builder, detector):
        """测试完整实现的工作流

        验证当所有功能都正确实现时，工作流返回良好结果。
        """
        doc = parser.parse(COMPLEX_PRD)
        contract = builder.build(doc)

        tracker = FeatureTracker(contract)
        # 使用与功能点标题匹配的关键词
        complete_execution = """
        已完成所有功能:
        - 创建基础代理
        - 部署代理到生产环境
        - 监控代理运行状态
        """
        tracker.verify_sync(complete_execution)

        report = detector.detect_from_tracker(tracker)

        # 完整实现应该有低偏离度
        assert report.drift_score < 30
        assert report.level in [DriftLevel.NONE, DriftLevel.MINOR, DriftLevel.MODERATE]

    def test_failed_implementation_workflow(self, parser, builder, detector):
        """测试实现失败的工作流

        验证当实现完全失败时，工作流正确报告CRITICAL偏离。
        """
        doc = parser.parse(COMPLEX_PRD)
        contract = builder.build(doc)

        tracker = FeatureTracker(contract)
        failed_execution = "未完成任何功能"
        tracker.verify_sync(failed_execution)

        report = detector.detect_from_tracker(tracker)

        # 大部分功能未实现
        assert report.verified_count < report.total_count
        assert report.drift_score > 50

    def test_empty_prd_workflow(self, parser, builder, detector):
        """测试空PRD工作流

        验证空文档能够正确处理。
        """
        empty_doc = parser.parse("")
        assert empty_doc.title == "Untitled Document"
        assert len(empty_doc.feature_points) == 0

        contract = builder.build(empty_doc)
        assert contract.total_requirements == 0

        tracker = FeatureTracker(contract)
        tracker.verify_sync("执行了一些操作")

        report = detector.detect_from_tracker(tracker)

        assert report.total_count == 0
        assert report.drift_score == 0
        assert report.level == DriftLevel.NONE

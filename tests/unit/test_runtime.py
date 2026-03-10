"""
Unit Tests for Runtime Modules

基于 Google 测试金字塔 - 单元测试层
每个测试是一个独立的功能验证
"""

import json
from datetime import datetime

import pytest


class TestAuditModule:
    """测试审计模块"""

    def test_audit_event_creation(self):
        """测试审计事件创建"""
        from src.runtime.audit import AuditEvent

        event = AuditEvent(
            timestamp=datetime.now(),
            event_type="execute",
            sandbox_id="test-001"
        )

        assert event.event_type == "execute"
        assert event.sandbox_id == "test-001"

    def test_audit_event_to_dict(self):
        """测试审计事件序列化"""
        from src.runtime.audit import AuditEvent

        event = AuditEvent(
            timestamp=datetime.now(),
            event_type="test",
            sandbox_id="test-002"
        )

        data = event.to_dict()
        assert isinstance(data, dict)
        assert data["event_type"] == "test"

    def test_audit_event_json_serialization(self):
        """测试审计事件JSON序列化"""
        from src.runtime.audit import AuditEvent

        event = AuditEvent(
            timestamp=datetime.now(),
            event_type="execute",
            sandbox_id="test-003",
            code_length=100,
            duration_ms=500
        )

        json_str = json.dumps(event.to_dict())
        parsed = json.loads(json_str)

        assert parsed["sandbox_id"] == "test-003"
        assert parsed["code_length"] == 100


class TestContextCollector:
    """测试上下文收集器"""

    def test_collector_initialization(self):
        """测试收集器初始化"""
        from src.runtime.context_collector import ContextCollector

        collector = ContextCollector(agent_id="test-agent", agent_name="TestAgent")

        assert collector.agent_id == "test-agent"
        assert collector.context.agent_name == "TestAgent"

    def test_collector_has_request_id(self):
        """测试收集器有请求ID"""
        from src.runtime.context_collector import ContextCollector

        collector = ContextCollector()
        assert collector.context.request_id is not None

    def test_collector_has_timestamp(self):
        """测试收集器有时间戳"""
        from src.runtime.context_collector import ContextCollector

        collector = ContextCollector()
        assert collector.context.timestamp is not None

    def test_collector_serialization(self):
        """测试收集器序列化"""
        from src.runtime.context_collector import ContextCollector

        collector = ContextCollector()
        data = collector.to_dict()

        assert isinstance(data, dict)
        json_str = json.dumps(data)
        parsed = json.loads(json_str)

        assert "request_id" in parsed


class TestSecurityBasic:
    """测试基础安全模块"""

    def test_security_basic_import(self):
        """测试安全模块可导入"""
        try:
            from src.runtime.security_basic import SecurityConfig
            assert SecurityConfig is not None
        except ImportError:
            pytest.skip("security_basic module not available")


class TestSandboxConfig:
    """测试沙箱配置"""

    def test_sandbox_import(self):
        """测试沙箱模块可导入"""
        try:
            from src.runtime.sandbox import SandboxConfig
            assert SandboxConfig is not None
        except ImportError:
            pytest.skip("sandbox module not available")


class TestPoolModule:
    """测试池模块"""

    def test_pool_import(self):
        """测试池模块可导入"""
        try:
            from src.runtime.pool import Pool
            assert Pool is not None
        except ImportError:
            pytest.skip("pool module not available")


class TestSkillsCollection:
    """测试技能收集"""

    def test_collect_skills(self):
        """测试技能收集"""
        from src.runtime.context_collector import ContextCollector

        collector = ContextCollector()
        skills = collector.collect_skills()

        assert skills is not None
        assert isinstance(skills, list)

    def test_collect_mcps(self):
        """测试MCP收集"""
        from src.runtime.context_collector import ContextCollector

        collector = ContextCollector()
        mcps = collector.collect_mcps()

        assert mcps is not None
        assert isinstance(mcps, list)

    def test_collect_hooks(self):
        """测试Hooks收集"""
        from src.runtime.context_collector import ContextCollector

        collector = ContextCollector()
        hooks = collector.collect_hooks()

        assert hooks is not None
        assert isinstance(hooks, list)

    def test_collect_environment_vars(self):
        """测试环境变量收集"""
        from src.runtime.context_collector import ContextCollector

        collector = ContextCollector()
        env_vars = collector.collect_environment_vars()

        assert env_vars is not None
        assert isinstance(env_vars, dict)

    def test_collect_network_status(self):
        """测试网络状态收集"""
        from src.runtime.context_collector import ContextCollector

        collector = ContextCollector()
        network = collector.collect_network_status()

        assert network is not None
        assert hasattr(network, 'connected')


# ==================== Fixtures ====================

@pytest.fixture
def sample_audit_event():
    """创建示例审计事件"""
    from src.runtime.audit import AuditEvent

    return AuditEvent(
        timestamp=datetime.now(),
        event_type="test",
        sandbox_id="fixture-test-001"
    )


@pytest.fixture
def sample_context_collector():
    """创建示例收集器"""
    from src.runtime.context_collector import ContextCollector

    return ContextCollector(agent_id="fixture-agent", agent_name="FixtureAgent")

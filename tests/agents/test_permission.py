"""
PermissionEvaluator Tests - Task 2.3
"""

import pytest

from src.agents.permission import PermissionEvaluator
from src.core.types import (
    PermissionAction,
    PermissionConfig,
    PermissionRule,
)


class TestPermissionEvaluator:
    """Test PermissionEvaluator - Task 2.3"""

    @pytest.fixture
    def default_config(self):
        return PermissionConfig(_global=PermissionAction.ASK)

    @pytest.fixture
    def evaluator(self, default_config):
        return PermissionEvaluator(default_config)

    @pytest.mark.asyncio
    async def test_default_ask(self, evaluator):
        """测试默认询问"""
        action = await evaluator.check("bash", {})
        assert action == PermissionAction.ASK

    @pytest.mark.asyncio
    async def test_exact_tool_match(self, evaluator):
        """测试精确工具匹配"""
        rule = PermissionRule(tool_pattern="bash", action=PermissionAction.DENY)
        evaluator.add_rule(rule)

        action = await evaluator.check("bash", {})
        assert action == PermissionAction.DENY

        # 其他工具仍返回默认
        action = await evaluator.check("read", {})
        assert action == PermissionAction.ASK

    @pytest.mark.asyncio
    async def test_wildcard_tool_match(self, evaluator):
        """测试通配符工具匹配"""
        rule = PermissionRule(tool_pattern="write*", action=PermissionAction.DENY)
        evaluator.add_rule(rule)

        action = await evaluator.check("write", {"filePath": "test.py"})
        assert action == PermissionAction.DENY

    @pytest.mark.asyncio
    async def test_params_match(self, evaluator):
        """测试参数匹配"""
        rule = PermissionRule(
            tool_pattern="bash",
            params_pattern={"command": "rm -rf*"},
            action=PermissionAction.DENY,
        )
        evaluator.add_rule(rule)

        # 匹配危险命令
        action = await evaluator.check("bash", {"command": "rm -rf /tmp"})
        assert action == PermissionAction.DENY

        # 不匹配普通命令
        action = await evaluator.check("bash", {"command": "ls"})
        assert action == PermissionAction.ASK

    @pytest.mark.asyncio
    async def test_check_with_confirm(self, evaluator):
        """测试带确认的检查"""
        action, msg = await evaluator.check_with_confirm("bash", {})
        assert action == PermissionAction.ASK
        assert msg == "确认执行此操作?"

        # ALLOW 不返回确认消息
        evaluator.set_global(PermissionAction.ALLOW)
        action, msg = await evaluator.check_with_confirm("bash", {})
        assert action == PermissionAction.ALLOW
        assert msg is None

    def test_add_rule(self, evaluator):
        """测试添加规则"""
        rule = PermissionRule(tool_pattern="test", action=PermissionAction.ALLOW)
        evaluator.add_rule(rule)

        assert len(evaluator.permission.rules) == 1

    def test_remove_rule(self, evaluator):
        """测试移除规则"""
        rule = PermissionRule(tool_pattern="test", action=PermissionAction.ALLOW)
        evaluator.add_rule(rule)

        evaluator.remove_rule("test")

        assert len(evaluator.permission.rules) == 0

    def test_set_global(self, evaluator):
        """测试设置全局默认"""
        evaluator.set_global(PermissionAction.DENY)
        assert evaluator.permission._global == PermissionAction.DENY

    @pytest.mark.asyncio
    async def test_create_allow_all(self):
        """测试创建允许所有的评估器"""
        evaluator = PermissionEvaluator.create_allow_all()

        action = await evaluator.check("bash", {})
        assert action == PermissionAction.ALLOW

    @pytest.mark.asyncio
    async def test_create_deny_all(self):
        """测试创建拒绝所有的评估器"""
        evaluator = PermissionEvaluator.create_deny_all()

        action = await evaluator.check("bash", {})
        assert action == PermissionAction.DENY

    @pytest.mark.asyncio
    async def test_can_run(self, evaluator):
        """测试 can_run"""
        result = await evaluator.can_run("Hello")
        assert result is True

"""
Policy Engine Tests - Phase 2.4
Tests for Security Policy Engine
"""

import pytest
from src.runtime.security.policy import (
    PolicyEngine,
    Policy,
    PolicyRule,
    PolicyAction,
    PolicyEffect,
    create_strict_policy,
    create_standard_policy,
    create_permissive_policy,
)


class TestPolicyRule:
    """PolicyRule 测试"""

    def test_basic_rule(self):
        """基本规则测试"""
        rule = PolicyRule(
            name="test_rule",
            description="Test rule",
            patterns=[r"evil", r"bad"],
            action=PolicyAction.DENY,
            priority=10,
        )

        # 匹配
        assert rule.matches({"content": "this is evil"}) == True
        # 不匹配
        assert rule.matches({"content": "this is good"}) == False

    def test_condition_function(self):
        """条件函数测试"""
        rule = PolicyRule(
            name="test_rule",
            description="Test rule",
            condition=lambda ctx: ctx.get("user_level", 0) >= 5,
            action=PolicyAction.ALLOW,
        )

        assert rule.matches({"user_level": 5}) == True
        assert rule.matches({"user_level": 1}) == False

    def test_disabled_rule(self):
        """禁用规则测试"""
        rule = PolicyRule(
            name="test_rule",
            description="Test rule",
            patterns=[r"test"],
            enabled=False,
        )

        assert rule.matches({"content": "test"}) == False


class TestPolicy:
    """Policy 测试"""

    def test_add_rule(self):
        """添加规则测试"""
        policy = Policy(name="test", description="Test policy")

        rule1 = PolicyRule(name="rule1", description="", priority=10)
        rule2 = PolicyRule(name="rule2", description="", priority=5)

        policy.add_rule(rule1)
        policy.add_rule(rule2)

        # 应该按优先级排序
        assert policy.rules[0].name == "rule2"
        assert policy.rules[1].name == "rule1"

    def test_evaluate_with_match(self):
        """评估 - 匹配规则"""
        policy = Policy(
            name="test",
            description="Test",
            default_action=PolicyAction.DENY,
        )

        policy.add_rule(PolicyRule(
            name="allow_print",
            description="",
            patterns=[r"print\("],
            action=PolicyAction.ALLOW,
            priority=10,
        ))

        action, rule_name = policy.evaluate({"content": "print('hello')"})
        assert action == PolicyAction.ALLOW
        assert rule_name == "allow_print"

    def test_evaluate_no_match(self):
        """评估 - 无匹配"""
        policy = Policy(
            name="test",
            description="Test",
            default_action=PolicyAction.ALLOW,
        )

        action, rule_name = policy.evaluate({"content": "unknown"})
        assert action == PolicyAction.ALLOW
        assert rule_name is None


class TestPolicyEngine:
    """PolicyEngine 测试"""

    def test_add_policy(self):
        """添加策略测试"""
        engine = PolicyEngine()
        policy = Policy(name="test", description="Test")

        engine.add_policy(policy)
        assert engine.get_policy("test") == policy

    def test_remove_policy(self):
        """移除策略测试"""
        engine = PolicyEngine()
        policy = Policy(name="test", description="Test")
        engine.add_policy(policy)

        assert engine.remove_policy("test") == True
        assert engine.get_policy("test") is None

    def test_default_policy(self):
        """默认策略测试"""
        engine = PolicyEngine()

        policy1 = Policy(name="policy1", description="")
        policy2 = Policy(name="policy2", description="")

        engine.add_policy(policy1)
        engine.add_policy(policy2)

        # 第一个添加的应该是默认策略
        assert engine._default_policy.name == "policy1"

    def test_evaluate(self):
        """评估测试"""
        engine = PolicyEngine()

        policy = Policy(
            name="test",
            description="Test",
            default_action=PolicyAction.DENY,
        )
        policy.add_rule(PolicyRule(
            name="allow",
            description="",
            patterns=[r"^print"],  # Use word boundary pattern
            action=PolicyAction.ALLOW,
        ))

        engine.add_policy(policy)

        action, rule = engine.evaluate({"content": "print('hello')"})
        assert action == PolicyAction.ALLOW

        action, rule = engine.evaluate({"content": "eval('x')"})
        assert action == PolicyAction.DENY


class TestPrebuiltPolicies:
    """预建策略测试"""

    def test_strict_policy(self):
        """严格策略测试"""
        policy = create_strict_policy()

        # 危险代码应该被拒绝
        action, _ = policy.evaluate({"content": "eval('dangerous')"})
        assert action == PolicyAction.DENY

        # 安全代码应该被允许
        action, _ = policy.evaluate({"content": "print('hello')"})
        assert action == PolicyAction.ALLOW

    def test_standard_policy(self):
        """标准策略测试"""
        policy = create_standard_policy()

        # 常规代码应该被允许
        action, _ = policy.evaluate({"content": "print('hello')"})
        assert action == PolicyAction.ALLOW

        # 危险操作应该警告
        action, _ = policy.evaluate({"content": "eval('x')"})
        assert action == PolicyAction.WARN

    def test_permissive_policy(self):
        """宽松策略测试"""
        policy = create_permissive_policy()

        # 大部分应该被允许
        action, _ = policy.evaluate({"content": "print('hello')"})
        assert action == PolicyAction.ALLOW


class TestPolicyAction:
    """PolicyAction 枚举测试"""

    def test_actions(self):
        """动作枚举测试"""
        assert PolicyAction.ALLOW.value == "allow"
        assert PolicyAction.DENY.value == "deny"
        assert PolicyAction.WARN.value == "warn"
        assert PolicyAction.SANITIZE.value == "sanitize"
        assert PolicyAction.AUDIT.value == "audit"


class TestPolicyIntegration:
    """策略集成测试"""

    def test_context_evaluation(self):
        """上下文评估测试"""
        policy = create_standard_policy()

        # 带有检测到注入的上下文
        context = {
            "content": "normal code",
            "detected_injection": True,
        }
        action, rule = policy.evaluate(context)
        assert action == PolicyAction.DENY

    def test_multiple_patterns(self):
        """多模式匹配测试"""
        rule = PolicyRule(
            name="multi",
            description="",
            patterns=[r"exec\(", r"eval\(", r"__import__\("],
            action=PolicyAction.DENY,
        )

        policy = Policy(
            name="test",
            description="",
            default_action=PolicyAction.ALLOW,
        )
        policy.add_rule(rule)

        assert rule.matches({"content": "exec('x')"}) == True
        assert rule.matches({"content": "eval('x')"}) == True
        assert rule.matches({"content": "__import__('os')"}) == True

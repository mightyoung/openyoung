"""
安全策略引擎

定义和执行安全策略规则
"""

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Optional


class PolicyAction(str, Enum):
    """策略动作"""

    ALLOW = "allow"  # 允许执行
    DENY = "deny"  # 拒绝执行
    WARN = "warn"  # 警告但允许
    SANITIZE = "sanitize"  # 清理后执行
    AUDIT = "audit"  # 仅记录审计


class PolicyEffect(str, Enum):
    """策略效果"""

    PERMIT = "permit"  # 允许
    DENY = "deny"  # 拒绝


@dataclass
class PolicyRule:
    """策略规则"""

    name: str
    description: str

    # 匹配条件
    condition: Callable[[dict], bool] = field(default=lambda _: True)

    # 匹配模式 (可选的简化的条件)
    patterns: list[str] = field(default_factory=list)

    # 匹配的资源类型
    resource_type: Optional[str] = None  # code, network, file, api

    # 动作
    action: PolicyAction = PolicyAction.ALLOW

    # 优先级 (数字越小优先级越高)
    priority: int = 100

    # 是否启用
    enabled: bool = True

    def matches(self, context: dict) -> bool:
        """
        检查上下文是否匹配此规则

        Args:
            context: 安全上下文

        Returns:
            是否匹配
        """
        if not self.enabled:
            return False

        # 先检查条件函数
        if not self.condition(context):
            return False

        # 检查模式匹配
        if self.patterns:
            content = context.get("content", "")
            for pattern in self.patterns:
                if re.search(pattern, content):
                    return True
            return False

        return True


@dataclass
class Policy:
    """安全策略"""

    name: str
    description: str
    version: str = "1.0"
    enabled: bool = True

    # 策略规则
    rules: list[PolicyRule] = field(default_factory=list)

    # 默认动作 (当没有规则匹配时)
    default_action: PolicyAction = PolicyAction.ALLOW

    # 元数据
    metadata: dict = field(default_factory=dict)

    def add_rule(self, rule: PolicyRule) -> None:
        """添加规则"""
        self.rules.append(rule)
        # 按优先级排序
        self.rules.sort(key=lambda r: r.priority)

    def evaluate(self, context: dict) -> tuple[PolicyAction, Optional[str]]:
        """
        评估上下文，返回应执行的动作

        Args:
            context: 安全上下文

        Returns:
            (action, matched_rule_name)
        """
        for rule in self.rules:
            if rule.matches(context):
                return rule.action, rule.name

        return self.default_action, None


class PolicyEngine:
    """策略引擎

    管理多个安全策略并执行评估
    """

    def __init__(self):
        self._policies: dict[str, Policy] = {}
        self._default_policy: Optional[Policy] = None

    def add_policy(self, policy: Policy) -> None:
        """
        添加策略

        Args:
            policy: 策略对象
        """
        self._policies[policy.name] = policy
        if self._default_policy is None:
            self._default_policy = policy

    def remove_policy(self, name: str) -> bool:
        """
        移除策略

        Args:
            name: 策略名称

        Returns:
            是否成功移除
        """
        if name in self._policies:
            del self._policies[name]
            return True
        return False

    def get_policy(self, name: str) -> Optional[Policy]:
        """获取策略"""
        return self._policies.get(name)

    def set_default_policy(self, name: str) -> bool:
        """
        设置默认策略

        Args:
            name: 策略名称

        Returns:
            是否成功设置
        """
        if name in self._policies:
            self._default_policy = self._policies[name]
            return True
        return False

    def evaluate(
        self, context: dict, policy_name: Optional[str] = None
    ) -> tuple[PolicyAction, Optional[str]]:
        """
        评估上下文

        Args:
            context: 安全上下文
            policy_name: 策略名称，None 表示使用默认策略

        Returns:
            (action, matched_rule_name)
        """
        policy = self._policies.get(policy_name) if policy_name else self._default_policy

        if policy is None:
            return PolicyAction.ALLOW, None

        return policy.evaluate(context)

    def list_policies(self) -> list[str]:
        """列出所有策略"""
        return list(self._policies.keys())

    def enable_policy(self, name: str) -> bool:
        """启用策略"""
        policy = self._policies.get(name)
        if policy:
            policy.enabled = True
            return True
        return False

    def disable_policy(self, name: str) -> bool:
        """禁用策略"""
        policy = self._policies.get(name)
        if policy:
            policy.enabled = False
            return True
        return False


# ========== Convenience Functions ==========


def create_policy(
    name: str,
    description: str,
    rules: list[PolicyRule] = None,
    default_action: PolicyAction = PolicyAction.ALLOW,
) -> Policy:
    """
    便捷函数：创建策略

    Args:
        name: 策略名称
        description: 策略描述
        rules: 规则列表
        default_action: 默认动作

    Returns:
        Policy 实例
    """
    return Policy(
        name=name,
        description=description,
        rules=rules or [],
        default_action=default_action,
    )


def create_rule(
    name: str,
    description: str,
    condition: Callable[[dict], bool] = None,
    patterns: list[str] = None,
    action: PolicyAction = PolicyAction.DENY,
    priority: int = 100,
) -> PolicyRule:
    """
    便捷函数：创建策略规则

    Args:
        name: 规则名称
        description: 规则描述
        condition: 条件函数
        patterns: 匹配模式
        action: 动作
        priority: 优先级

    Returns:
        PolicyRule 实例
    """
    return PolicyRule(
        name=name,
        description=description,
        condition=condition or (lambda _: True),
        patterns=patterns or [],
        action=action,
        priority=priority,
    )


# ========== Pre-built Policies ==========


def create_strict_policy() -> Policy:
    """创建严格策略 - 默认拒绝所有危险操作"""
    policy = Policy(
        name="strict",
        description="严格安全策略 - 默认拒绝所有可能危险的操作",
        default_action=PolicyAction.DENY,
    )

    # 允许的代码模式
    policy.add_rule(
        PolicyRule(
            name="allow_safe_code",
            description="允许安全的代码模式",
            patterns=[r"^print\(", r"^import ", r"^def ", r"^class "],
            action=PolicyAction.ALLOW,
            priority=10,
        )
    )

    # 拒绝危险操作
    policy.add_rule(
        PolicyRule(
            name="deny_dangerous_code",
            description="拒绝危险代码",
            patterns=[r"eval\(", r"exec\(", r"__import__\("],
            action=PolicyAction.DENY,
            priority=20,
        )
    )

    return policy


def create_standard_policy() -> Policy:
    """创建标准策略 - 平衡安全性和便利性"""
    policy = Policy(
        name="standard",
        description="标准安全策略 - 平衡安全性和便利性",
        default_action=PolicyAction.WARN,
    )

    # 允许常规代码
    policy.add_rule(
        PolicyRule(
            name="allow_normal_code",
            description="允许常规代码",
            patterns=[
                r"^print\(",
                r"^import ",
                r"^def ",
                r"^class ",
                r"^if ",
                r"^for ",
                r"^while ",
            ],
            action=PolicyAction.ALLOW,
            priority=10,
        )
    )

    # 警告危险操作
    policy.add_rule(
        PolicyRule(
            name="warn_dangerous",
            description="警告危险操作",
            patterns=[r"eval\(", r"exec\("],
            action=PolicyAction.WARN,
            priority=50,
        )
    )

    # 阻止提示注入
    policy.add_rule(
        PolicyRule(
            name="block_injection",
            description="阻止提示注入",
            condition=lambda ctx: ctx.get("detected_injection", False),
            action=PolicyAction.DENY,
            priority=5,
        )
    )

    return policy


def create_permissive_policy() -> Policy:
    """创建宽松策略 - 最小限制"""
    policy = Policy(
        name="permissive",
        description="宽松安全策略 - 最小限制",
        default_action=PolicyAction.ALLOW,
    )

    # 只阻止最明显的危险操作
    policy.add_rule(
        PolicyRule(
            name="block_extreme_danger",
            description="阻止极端危险操作",
            patterns=[r"rm\s+-rf\s+/", r"format\s+disk", r"drop\s+table"],
            action=PolicyAction.DENY,
            priority=1,
        )
    )

    return policy

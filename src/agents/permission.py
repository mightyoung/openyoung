"""
PermissionEvaluator - 权限评估器
对标 OpenCode PermissionNext，实现 ask/allow/deny 三级权限控制
"""

import fnmatch
from typing import Optional

from src.core.types import (
    PermissionConfig,
    PermissionAction,
    PermissionRule,
)


class PermissionEvaluator:
    """权限评估器 - 对标 OpenCode

    实现三级权限控制：
    - ALLOW: 无需批准直接执行
    - ASK: 提示用户确认
    - DENY: 阻止执行
    """

    def __init__(self, permission: PermissionConfig):
        self.permission = permission

    async def can_run(self, user_input: str) -> bool:
        """检查是否允许运行（主 Agent 级别）"""
        return True

    async def check(self, tool_name: str, params: dict) -> PermissionAction:
        """检查工具权限

        Args:
            tool_name: 工具名称
            params: 工具参数字典

        Returns:
            PermissionAction: ALLOW, ASK, 或 DENY
        """

        # 1. 按顺序检查规则
        for rule in self.permission.rules:
            if self._match_rule(tool_name, params, rule):
                return rule.action

        # 2. 返回全局默认
        return self.permission._global

    async def check_with_confirm(
        self, tool_name: str, params: dict
    ) -> tuple[PermissionAction, Optional[str]]:
        """检查权限并返回确认消息

        Returns:
            (action, confirm_message): 权限动作和确认消息
        """
        action = await self.check(tool_name, params)

        if action == PermissionAction.ASK:
            return (action, self.permission.confirm_message)

        return (action, None)

    def _match_rule(self, tool_name: str, params: dict, rule: PermissionRule) -> bool:
        """匹配规则

        支持：
        - 精确匹配: "bash"
        - 通配符匹配: "bash:*", "write:*", "*"
        - 参数匹配: rule.params_pattern
        """

        # 1. 工具名匹配（支持通配符）
        if not fnmatch.fnmatch(tool_name, rule.tool_pattern):
            return False

        # 2. 参数模式匹配（如果指定了）
        if rule.params_pattern:
            return self._match_params(params, rule.params_pattern)

        return True

    def _match_params(self, params: dict, pattern: dict) -> bool:
        """匹配参数模式

        例如:
        - pattern = {"command": "rm -rf*"} 匹配删除命令
        - pattern = {"filePath": "*.py"} 匹配 Python 文件
        """

        for key, expected_value in pattern.items():
            if key not in params:
                return False

            actual_value = params[key]

            # 支持通配符匹配
            if isinstance(expected_value, str) and isinstance(actual_value, str):
                if not fnmatch.fnmatch(actual_value, expected_value):
                    return False
            elif actual_value != expected_value:
                return False

        return True

    def add_rule(self, rule: PermissionRule):
        """动态添加规则"""
        self.permission.rules.append(rule)

    def remove_rule(self, tool_pattern: str):
        """移除指定工具的规则"""
        self.permission.rules = [
            r for r in self.permission.rules if r.tool_pattern != tool_pattern
        ]

    def set_global(self, action: PermissionAction):
        """设置全局默认权限"""
        self.permission._global = action

    @staticmethod
    def create_allow_all() -> "PermissionEvaluator":
        """创建允许所有的权限评估器"""
        config = PermissionConfig(_global=PermissionAction.ALLOW)
        return PermissionEvaluator(config)

    @staticmethod
    def create_deny_all() -> "PermissionEvaluator":
        """创建拒绝所有的权限评估器"""
        config = PermissionConfig(_global=PermissionAction.DENY)
        return PermissionEvaluator(config)

    @staticmethod
    def create_ask_all() -> "PermissionEvaluator":
        """创建询问所有的权限评估器"""
        config = PermissionConfig(_global=PermissionAction.ASK)
        return PermissionEvaluator(config)


class PermissionAskError(Exception):
    """需要用户确认的异常"""

    def __init__(self, tool_name: str, params: dict, message: str = ""):
        self.tool_name = tool_name
        self.params = params
        self.message = message or f"Permission required: {tool_name} with params {params}"
        super().__init__(self.message)


class PermissionDeniedError(Exception):
    """权限被拒绝的异常"""

    def __init__(self, tool_name: str, params: dict):
        self.tool_name = tool_name
        self.params = params
        super().__init__(f"Permission denied: {tool_name}")


async def request_user_confirmation(tool_name: str, params: dict, message: str) -> bool:
    """请求用户确认 - 交互式确认
    
    在实际实现中，这应该连接到 CLI 或 UI 的确认流程
    
    Returns:
        True if user confirms, False otherwise
    """
    # 构建确认消息
    confirm_msg = "\n⚠️  Permission Request\n"
    confirm_msg += f"Tool: {tool_name}\n"
    confirm_msg += f"Params: {params}\n"
    confirm_msg += f"\n{message}\n"
    confirm_msg += "\nAllow this operation? [y/N]: "
    
    # 在交互式环境中请求确认
    try:
        response = input(confirm_msg).strip().lower()
        return response in ('y', 'yes')
    except (EOFError, KeyboardInterrupt):
        # 非交互式环境默认拒绝
        return False

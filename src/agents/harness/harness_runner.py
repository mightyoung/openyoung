"""
Harness Runner - Harness Lifecycle Management

提取自 young_agent.py 的 Harness 相关操作。
封装 Harness 的启动、记录步骤、状态获取和数据持久化。
"""

from typing import Any


class HarnessRunner:
    """Harness 执行引擎 - 封装 Harness 的生命周期管理

    YoungAgent 使用 Harness 来跟踪任务执行步骤和质量评分。
    """

    def __init__(self, harness=None):
        """初始化 HarnessRunner

        Args:
            harness: Harness 实例，如果为 None 则延迟创建
        """
        self._harness = harness

    def start(self) -> None:
        """启动 Harness"""
        if self._harness:
            self._harness.start()

    def record_step(self, success: bool) -> None:
        """记录执行步骤

        Args:
            success: 步骤是否成功
        """
        if self._harness:
            self._harness.record_step(success)

    def get_status(self) -> dict[str, Any]:
        """获取 Harness 状态

        Returns:
            Harness 状态字典
        """
        if self._harness:
            return self._harness.get_status()
        return {}

    def save(self, path: str) -> None:
        """保存 Harness 状态

        Args:
            path: 保存路径
        """
        if self._harness:
            self._harness.save(path)

    @property
    def harness(self):
        """获取 Harness 实例"""
        return self._harness

    def set_harness(self, harness) -> None:
        """设置 Harness 实例

        Args:
            harness: Harness 实例
        """
        self._harness = harness

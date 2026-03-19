"""
YoungAgent Checkpoint and Hooks Methods

提取自 young_agent.py 的检查点和 Hooks 相关方法。
"""

from typing import Any


async def save_checkpoint(self, file_path: str = None, reason: str = "task_complete") -> None:
    """保存检查点"""
    if not self._checkpoint_manager:
        return

    try:
        # 保存任务状态
        state = {
            "session_id": self._session_id,
            "history_count": len(self._history),
            "stats": self._stats,
        }

        checkpoint_id = await self._checkpoint_manager.create_checkpoint(
            file_path=file_path or self._data_dir + "/state.json",
            reason=reason,
        )
        if checkpoint_id:
            print(f"[Checkpoint] Created: {checkpoint_id}")
    except Exception as e:
        self._logger.warning(f"Checkpoint save failed: {e}")


def trigger_hooks(self, trigger: str, context: dict = None) -> list[dict[str, Any]]:
    """触发指定类型的 hooks"""
    triggered = []

    # 1. 触发内置的自学习 Hook
    if trigger == "post_task" and context:
        try:
            from src.package_manager.hooks_loader import LearningHook

            learning_hook = LearningHook()
            result = learning_hook.on_post_task(context)
            if result.get("status") == "success":
                print(f"[LearningHook] Evolution triggered: {result.get('signals', [])}")
                if result.get("capsule_created"):
                    print(f"[LearningHook] Capsule created: {result.get('capsule_id')}")
            triggered.append({"hook": "learning_hook", "trigger": trigger, "action": "evolve"})
        except Exception as e:
            print(f"[LearningHook] Error: {e}")

    # 2. 触发配置的 hooks
    if self._hooks_loader and self._hooks:
        try:
            hooks = self._hooks_loader.get_hooks_by_trigger(trigger)
            for hook in hooks:
                triggered.append(
                    {
                        "hook": hook.name,
                        "trigger": trigger,
                        "action": hook.action.value if hook.action else None,
                    }
                )
                print(f"[Hooks] Triggered: {hook.name} ({trigger})")
        except Exception as e:
            self._logger.warning(f"Hook trigger failed: {e}")

    return triggered

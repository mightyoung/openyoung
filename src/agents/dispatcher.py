"""
TaskDispatcher - 任务调度器
对标 OpenCode task.ts，实现 SubAgent 系统
"""

import uuid

from src.agents.sub_agent import SubAgent
from src.core.types import (
    SubAgentType,
    Task,
    TaskDispatchParams,
)


class Session:
    """SubAgent 会话"""

    def __init__(self, session_id: str, parent_id: str | None, title: str):
        self.session_id = session_id
        self.parent_id = parent_id
        self.title = title
        self.messages = []

    def add_message(self, role: str, content: str):
        self.messages.append({"role": role, "content": content})


class TaskDispatcher:
    """任务调度器 - 对标 OpenCode

    核心职责：
    1. 管理 SubAgent 会话生命周期
    2. 构建隔离上下文
    3. 调度任务到合适的 SubAgent
    4. 聚合结果返回
    """

    def __init__(self, sub_agents: dict[str, SubAgent]):
        self.sub_agents = sub_agents
        self._sessions: dict[str, Session] = {}

    async def dispatch(
        self,
        params: TaskDispatchParams,
        parent_context: dict,
        existing_task_id: str | None = None,
    ) -> dict:
        """调度任务到 SubAgent

        Args:
            params: 任务调度参数
            parent_context: 父级上下文
            existing_task_id: 现有任务ID（用于恢复）

        Returns:
            dict: 包含 task_id, result, output, status
        """

        # 1. 获取或恢复会话
        session_id = await self._get_or_create_session(
            existing_task_id, parent_context.get("session_id"), params.task_description
        )

        # 2. 构建隔离上下文
        context = self._build_isolated_context(params, parent_context)

        # 3. 获取 SubAgent（按类型查找）
        sub_agent = await self._get_subagent(params.subagent_type)
        if not sub_agent:
            raise ValueError(f"Unknown subagent_type: {params.subagent_type}")

        # 4. 创建任务
        task = Task(
            id=session_id,
            description=params.task_description,
            input=params.task_description,
            subagent_type=params.subagent_type,
        )

        # 5. 执行任务
        result = await sub_agent.run(task, context)

        # 6. 返回结果
        return {
            "task_id": session_id,
            "result": result,
            "output": self._format_output(result),
            "status": "completed",
        }

    async def _get_or_create_session(
        self, task_id: str | None, parent_session_id: str | None, description: str
    ) -> str:
        """获取或创建会话"""
        if task_id and task_id in self._sessions:
            return task_id

        # 创建新的子会话
        new_session_id = task_id or str(uuid.uuid4())
        self._sessions[new_session_id] = Session(
            session_id=new_session_id,
            parent_id=parent_session_id,
            title=f"{description}",
        )
        return new_session_id

    def _build_isolated_context(self, params: TaskDispatchParams, parent_context: dict) -> dict:
        """构建隔离的上下文 - 对标 Claude Code

        SubAgent 运行在独立上下文中，不继承主 Agent 的完整历史
        只传递必要的摘要信息
        """
        return {
            "task_description": params.task_description,
            "parent_summary": parent_context.get("summary", ""),
            "relevant_files": parent_context.get("relevant_files", []),
            "session_id": parent_context.get("session_id"),
            "custom_context": params.context,
        }

    async def _get_subagent(self, subagent_type: SubAgentType) -> SubAgent | None:
        """获取 SubAgent - 按类型查找"""
        # 先按类型查找
        for agent in self.sub_agents.values():
            if agent.type == subagent_type:
                return agent
        return None

    def _format_output(self, result: str) -> str:
        """格式化输出 - 返回 Summary 而非完整输出"""
        # 对标 Claude Code：返回摘要而非完整输出
        if len(result) > 500:
            return result[:500] + "... [truncated]"
        return result

    def get_session(self, session_id: str) -> Session | None:
        """获取会话"""
        return self._sessions.get(session_id)

    def list_sessions(self) -> list[Session]:
        """列出所有会话"""
        return list(self._sessions.values())

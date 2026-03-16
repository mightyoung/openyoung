"""
Experience Engine - 经验引擎

负责收集、存储、检索经验的主引擎。
"""

import uuid
from datetime import datetime
from typing import Awaitable, Callable, List, Optional

from .embedding import QwenEmbeddingService
from .models import Action, ActionType, Experience, State, TaskCategory
from .rewards import RewardCalculator, RewardResult
from .store import ExperienceStore


# 事件类型
class ExperienceEvent:
    """经验事件"""

    EXPERIENCE_COLLECTED = "experience_collected"
    EXPERIENCE_STORED = "experience_stored"
    PATTERN_LEARNED = "pattern_learned"


# 事件处理器类型
EventHandler = Callable[[Experience], Awaitable[None]]


class ExperienceEngine:
    """经验引擎"""

    def __init__(
        self,
        store: Optional[ExperienceStore] = None,
        embedding_service: Optional[QwenEmbeddingService] = None,
        db_path: str = "data/experiences.db",
    ):
        self.store = store or ExperienceStore(db_path)
        self.embedding_service = embedding_service

        # 事件处理器
        self._event_handlers: dict[str, List[EventHandler]] = {
            ExperienceEvent.EXPERIENCE_COLLECTED: [],
            ExperienceEvent.EXPERIENCE_STORED: [],
            ExperienceEvent.PATTERN_LEARNED: [],
        }

        # 当前收集中的经验
        self._current_experience: Optional[Experience] = None
        self._current_states: List[State] = []
        self._current_actions: List[Action] = []

    def on(self, event: str, handler: EventHandler):
        """注册事件处理器"""
        if event in self._event_handlers:
            self._event_handlers[event].append(handler)

    async def _emit(self, event: str, experience: Experience):
        """触发事件"""
        for handler in self._event_handlers.get(event, []):
            try:
                await handler(experience)
            except Exception as e:
                # 记录错误但不中断
                print(f"Event handler error: {e}")

    # ============ 经验收集 API ============

    def start_collection(
        self,
        task_id: str,
        task_category: TaskCategory,
        task_description: str,
    ):
        """开始收集经验"""
        self._current_experience = Experience(
            id=str(uuid.uuid4()),
            task_id=task_id,
            task_category=task_category,
            task_description=task_description,
            created_at=datetime.now(),
        )
        self._current_states = []
        self._current_actions = []

    def add_state(self, content: str, category: str = "reasoning"):
        """添加状态（推理过程）"""
        if self._current_experience is None:
            raise RuntimeError("Not collecting experience")

        state = State(
            timestamp=datetime.now(),
            content=content,
            category=category,
        )
        self._current_states.append(state)

    def add_action(
        self,
        action_type: ActionType,
        name: str,
        input_data: dict = None,
        output_data=None,
        success: bool = True,
    ):
        """添加动作"""
        if self._current_experience is None:
            raise RuntimeError("Not collecting experience")

        action = Action(
            timestamp=datetime.now(),
            action_type=action_type,
            name=name,
            input_data=input_data or {},
            output_data=output_data,
            success=success,
        )
        self._current_actions.append(action)

    async def finish_collection(
        self,
        success: bool,
        evaluation_score: float = 0.0,
        completion_rate: float = 0.0,
        duration_ms: int = 0,
        token_count: int = 0,
        tool_call_count: int = 0,
        error_count: int = 0,
        generate_embedding: bool = True,
    ) -> Experience:
        """完成收集并保存经验"""
        if self._current_experience is None:
            raise RuntimeError("Not collecting experience")

        # 更新经验数据
        self._current_experience.states = self._current_states
        self._current_actions = self._current_actions
        self._current_experience.success = success
        self._current_experience.evaluation_score = evaluation_score
        self._current_experience.completion_rate = completion_rate
        self._current_experience.duration_ms = duration_ms
        self._current_experience.token_count = token_count
        self._current_experience.tool_call_count = tool_call_count
        self._current_experience.error_count = error_count

        # 计算奖励
        reward_result = RewardCalculator.compute(self._current_experience)
        self._current_experience.rewards = {
            "task_completion": reward_result.task_completion,
            "evaluation": reward_result.evaluation,
            "efficiency": reward_result.efficiency,
            "error_penalty": reward_result.error_penalty,
            "token_efficiency": reward_result.token_efficiency,
            "total": reward_result.total,
        }

        # 生成嵌入向量
        if generate_embedding and self.embedding_service:
            try:
                self._current_experience.embedding = await self.embedding_service.embed_experience(
                    self._current_experience
                )
            except Exception as e:
                print(f"Embedding generation failed: {e}")

        # 保存到存储
        await self.store.save(self._current_experience)

        # 触发事件
        await self._emit(ExperienceEvent.EXPERIENCE_COLLECTED, self._current_experience)
        await self._emit(ExperienceEvent.EXPERIENCE_STORED, self._current_experience)

        experience = self._current_experience

        # 重置
        self._current_experience = None
        self._current_states = []
        self._current_actions = []

        return experience

    def cancel_collection(self):
        """取消收集"""
        self._current_experience = None
        self._current_states = []
        self._current_actions = []

    # ============ 经验检索 API ============

    async def get_experience(self, experience_id: str) -> Optional[Experience]:
        """获取单条经验"""
        return await self.store.get(experience_id)

    async def query(
        self,
        task_category: Optional[TaskCategory] = None,
        success: Optional[bool] = None,
        min_score: Optional[float] = None,
        limit: int = 100,
    ) -> List[Experience]:
        """查询经验"""
        return await self.store.query(
            task_category=task_category,
            success=success,
            min_score=min_score,
            limit=limit,
        )

    async def get_failures(self, limit: int = 10) -> List[Experience]:
        """获取最近的失败经验"""
        return await self.store.get_recent_failures(limit)

    async def get_successful_patterns(
        self, task_category: TaskCategory, limit: int = 10
    ) -> List[Experience]:
        """获取成功模式"""
        return await self.store.get_successful_patterns(task_category, limit)

    async def find_similar(
        self, query: str, task_category: Optional[TaskCategory] = None, top_k: int = 5
    ) -> List[Experience]:
        """查找相似经验"""
        if not self.embedding_service:
            return []

        # 查询所有相关经验
        experiences = await self.query(
            task_category=task_category,
            success=True,  # 只查找成功经验
            limit=100,
        )

        # 查找相似
        return await self.embedding_service.find_similar(query, experiences, top_k)

    async def analyze_patterns(self, task_category: TaskCategory) -> dict:
        """分析任务模式"""
        successful = await self.get_successful_patterns(task_category, limit=20)
        failures = await self.query(task_category=task_category, success=False, limit=20)

        # 分析奖励分布
        successful_dist = RewardCalculator.analyze_reward_distribution(successful)
        failure_dist = RewardCalculator.analyze_reward_distribution(failures)

        return {
            "task_category": task_category.value,
            "successful_count": len(successful),
            "failure_count": len(failures),
            "successful_reward_dist": successful_dist,
            "failure_reward_dist": failure_dist,
        }

    async def update_stats(self):
        """更新统计信息"""
        await self.store.update_stats()

    # ============ 上下文管理器支持 ============

    async def collect(
        self,
        task_id: str,
        task_category: TaskCategory,
        task_description: str,
    ) -> "ExperienceCollector":
        """创建经验收集器（上下文管理器）"""
        return ExperienceCollector(self, task_id, task_category, task_description)


class ExperienceCollector:
    """经验收集器上下文管理器"""

    def __init__(
        self,
        engine: ExperienceEngine,
        task_id: str,
        task_category: TaskCategory,
        task_description: str,
    ):
        self.engine = engine
        self.task_id = task_id
        self.task_category = task_category
        self.task_description = task_description

    async def __aenter__(self):
        self.engine.start_collection(self.task_id, self.task_category, self.task_description)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            # 发生异常，取消收集
            self.engine.cancel_collection()
            return False

        # 完成任务收集
        # 参数由调用者通过 finish_collection 传递
        return False

    def add_state(self, content: str, category: str = "reasoning"):
        """添加状态"""
        self.engine.add_state(content, category)

    def add_action(
        self,
        action_type: ActionType,
        name: str,
        input_data: dict = None,
        output_data=None,
        success: bool = True,
    ):
        """添加动作"""
        self.engine.add_action(action_type, name, input_data, output_data, success)

"""
Knowledge Distillation - 知识蒸馏
从 Agent 提取和压缩知识
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime


@dataclass
class Knowledge:
    """知识表示"""

    experience_count: int = 0
    patterns: List[str] = field(default_factory=list)
    key_insights: List[str] = field(default_factory=list)
    action_patterns: List[str] = field(default_factory=list)
    success_patterns: List[str] = field(default_factory=list)
    compressed_representation: Optional[str] = None


class KnowledgeDistiller:
    """知识蒸馏器"""

    def __init__(self):
        self._knowledge_cache: Dict[str, Knowledge] = {}

    def extract(self, agent: Any) -> Knowledge:
        """从 Agent 提取知识"""
        knowledge = Knowledge()

        # 模拟知识提取
        if hasattr(agent, "name"):
            knowledge.experience_count = 1
            knowledge.patterns = [f"pattern_{agent.name}"]
            knowledge.key_insights = [f"insight_from_{agent.name}"]

        return knowledge

    def extract_from_history(
        self, execution_history: List[Dict[str, Any]]
    ) -> Knowledge:
        """从执行历史提取知识"""
        knowledge = Knowledge()

        knowledge.experience_count = len(execution_history)

        for item in execution_history:
            if "action" in item:
                knowledge.action_patterns.append(item["action"])
            if "result" in item and item.get("success"):
                knowledge.success_patterns.append(str(item["result"]))

        return knowledge

    def compress(self, knowledge: Knowledge) -> Knowledge:
        """压缩知识表示"""
        knowledge.compressed_representation = (
            f"compressed({len(knowledge.patterns)} patterns)"
        )
        return knowledge

    def get_knowledge(self, agent_id: str) -> Optional[Knowledge]:
        """获取缓存的知识"""
        return self._knowledge_cache.get(agent_id)

    def store_knowledge(self, agent_id: str, knowledge: Knowledge) -> None:
        """存储知识到缓存"""
        self._knowledge_cache[agent_id] = knowledge

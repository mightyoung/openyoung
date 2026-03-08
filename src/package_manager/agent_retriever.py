"""
Agent Retriever - Agent 语义搜索
支持关键词匹配、向量语义搜索、混合模式
"""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from .registry import AgentRegistry, AgentSpec


class SearchMode(Enum):
    """搜索模式"""
    KEYWORD = "keyword"      # 关键词匹配
    SEMANTIC = "semantic"  # 向量语义
    HYBRID = "hybrid"      # 混合模式


@dataclass
class SearchResult:
    """搜索结果"""
    agents: list[AgentSpec]
    mode: SearchMode
    total: int
    query: str


class AgentRetriever:
    """
    Agent 检索器

    支持三种搜索模式：
    1. KEYWORD - 关键词匹配（快速、精确）
    2. SEMANTIC - 向量语义（意图匹配）
    3. HYBRID - 混合模式（最佳效果）
    """

    def __init__(self, packages_dir: str = "packages", vector_store_path: str = None):
        self.packages_dir = Path(packages_dir)
        self._registry = AgentRegistry(packages_dir)
        self._cache: list[AgentSpec] = []

        # 初始化向量存储
        try:
            from src.memory.vector_store import VectorStore
            # 使用默认路径，让 VectorStore 使用自己的默认 db_path
            self._vector_store = VectorStore(vector_store_path)
        except Exception as e:
            print(f"[AgentRetriever] VectorStore init warning: {e}")
            self._vector_store = None

    # ========== 核心 API ==========

    async def search(
        self,
        query: str,
        mode: SearchMode = SearchMode.HYBRID,
        limit: int = 10,
        filters: dict[str, Any] | None = None
    ) -> SearchResult:
        """
        搜索 Agent

        Args:
            query: 搜索查询
            mode: 搜索模式
            limit: 返回数量限制
            filters: 过滤条件 {tags: [], tools: []}

        Returns:
            SearchResult: 搜索结果
        """
        # 刷新缓存
        await self._refresh_cache()

        # 根据模式选择搜索策略
        if mode == SearchMode.KEYWORD:
            agents = self._keyword_search(query, limit, filters)
        elif mode == SearchMode.SEMANTIC:
            agents = self._semantic_search(query, limit, filters)
        else:  # HYBRID
            agents = self._hybrid_search(query, limit, filters)

        return SearchResult(
            agents=agents,
            mode=mode,
            total=len(agents),
            query=query
        )

    def _keyword_search(
        self,
        query: str,
        limit: int,
        filters: dict | None
    ) -> list[AgentSpec]:
        """关键词匹配搜索"""
        query_lower = query.lower()

        results = []
        for agent in self._cache:
            # 检查是否匹配查询
            score = self._calculate_keyword_score(query_lower, agent)
            if score > 0:
                # 应用过滤
                if self._apply_filters(agent, filters):
                    # 存储匹配分数到临时属性
                    agent.quality_score = score
                    results.append(agent)

        # 按相关度排序
        results.sort(key=lambda a: getattr(a, 'quality_score', 0), reverse=True)
        return results[:limit]

    def _semantic_search(
        self,
        query: str,
        limit: int,
        filters: dict | None
    ) -> list[AgentSpec]:
        """向量语义搜索（真正的语义匹配）"""
        if not self._vector_store:
            print("[AgentRetriever] VectorStore not available, falling back to keyword")
            return self._keyword_search(query, limit, filters)

        try:
            # 1. 使用 VectorStore 搜索
            results = self._vector_store.search(
                query=query,
                namespace="agents",
                limit=limit * 2,
                threshold=0.0
            )

            if not results:
                print("[AgentRetriever] No semantic results, falling back to keyword")
                return self._keyword_search(query, limit, filters)

            # 2. 转换结果
            agents = []
            for r in results:
                import json
                tags_str = r.get("tags", "[]")
                # 解析 JSON 字符串
                try:
                    tags = json.loads(tags_str) if isinstance(tags_str, str) else tags_str
                except:
                    tags = []

                agent_name = tags[0] if tags else None

                if agent_name:
                    agent = self._registry.get_agent(agent_name)
                    if agent:
                        # 应用过滤
                        if self._apply_filters(agent, filters):
                            agent.quality_score = r.get("similarity", 0)
                            agents.append(agent)

            return agents[:limit]

        except Exception as e:
            print(f"[AgentRetriever] Semantic search error: {e}")
            return self._keyword_search(query, limit, filters)

    def _hybrid_search(
        self,
        query: str,
        limit: int,
        filters: dict | None
    ) -> list[AgentSpec]:
        """混合搜索：关键词 + 向量"""
        if not self._vector_store:
            # 向量存储不可用，回退到关键词
            return self._keyword_search(query, limit, filters)

        try:
            # 1. 关键词搜索
            keyword_results = self._keyword_search(query, limit * 2, filters)
            keyword_map = {a.name: getattr(a, 'quality_score', 0) for a in keyword_results}

            # 2. 语义搜索
            semantic_results = self._semantic_search(query, limit * 2, filters)
            semantic_map = {a.name: getattr(a, 'quality_score', 0) for a in semantic_results}

            # 3. 获取所有候选
            all_names = set(keyword_map.keys()) | set(semantic_map.keys())

            # 4. 混合评分
            combined = []
            for name in all_names:
                k_score = keyword_map.get(name, 0)
                s_score = semantic_map.get(name, 0)

                # 归一化：取两者的最大值作为基础
                max_score = max(k_score, s_score)

                # 如果两者都有分数，使用加权平均
                if k_score > 0 and s_score > 0:
                    final_score = k_score * 0.4 + s_score * 0.6
                else:
                    final_score = max_score

                agent = self._registry.get_agent(name)
                if agent:
                    agent.quality_score = final_score
                    combined.append(agent)

            # 5. 排序返回
            combined.sort(key=lambda a: getattr(a, 'quality_score', 0), reverse=True)
            return combined[:limit]

        except Exception as e:
            print(f"[AgentRetriever] Hybrid search error: {e}")
            return self._keyword_search(query, limit, filters)

    # ========== 辅助方法 ==========

    async def _refresh_cache(self):
        """刷新本地缓存"""
        self._cache = self._discover_agents()

    def _discover_agents(self) -> list[AgentSpec]:
        """发现所有已安装的 Agent"""
        return self._registry.discover_agents()

    def _apply_filters(self, agent: AgentSpec, filters: dict | None) -> bool:
        """应用过滤条件"""
        if not filters:
            return True

        if "tags" in filters:
            agent_tags = getattr(agent, 'tags', [])
            if not agent_tags or not any(t in agent_tags for t in filters["tags"]):
                return False

        if "tools" in filters:
            if not hasattr(agent, 'tools') or not agent.tools:
                return False
            if not any(t in agent.tools for t in filters["tools"]):
                return False

        return True

    def _calculate_keyword_score(self, query: str, agent: AgentSpec) -> float:
        """计算关键词匹配分数"""
        score = 0.0
        query_lower = query.lower()

        # name 匹配 - 最高权重
        if query_lower in agent.name.lower():
            score += 1.0

        # description 匹配
        if hasattr(agent, 'description') and agent.description:
            if query_lower in agent.description.lower():
                score += 0.5

        # tags 匹配
        if hasattr(agent, 'tags') and agent.tags:
            for tag in agent.tags:
                if query_lower in tag.lower():
                    score += 0.3

        # 归一化
        return min(score, 1.0)

    # ========== 便捷方法 ==========

    async def list_all(self) -> list[AgentSpec]:
        """列出所有已安装的 Agent"""
        await self._refresh_cache()
        return self._cache

    async def get_by_name(self, name: str) -> AgentSpec | None:
        """根据名称获取 Agent"""
        await self._refresh_cache()
        for agent in self._cache:
            if agent.name == name:
                return agent
        return None


# ========== 便捷函数 ==========

def create_retriever(packages_dir: str = "packages") -> AgentRetriever:
    """创建 AgentRetriever 实例"""
    return AgentRetriever(packages_dir)

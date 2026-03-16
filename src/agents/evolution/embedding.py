"""
Qwen Embedding Service - Qwen 向量嵌入服务

使用 DashScope API 生成文本嵌入。
"""

import asyncio
import os
from typing import Optional

try:
    from openai import AsyncOpenAI
except ImportError:
    # Fallback for environments without openai package
    AsyncOpenAI = None

from .models import Experience


class QwenEmbeddingService:
    """Qwen 向量嵌入服务"""

    DEFAULT_MODEL = "text-embedding-v3"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = DEFAULT_MODEL,
    ):
        self.api_key = api_key or os.environ.get("DASHSCOPE_API_KEY")
        self.model = model
        self._client: Optional[AsyncOpenAI] = None

    @property
    def client(self) -> AsyncOpenAI:
        """懒加载客户端"""
        if self._client is None:
            if AsyncOpenAI is None:
                raise ImportError("openai package required. Install with: pip install openai")
            self._client = AsyncOpenAI(
                api_key=self.api_key,
                base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            )
        return self._client

    async def embed(self, text: str) -> list[float]:
        """生成单个文本的嵌入向量"""
        if not self.api_key:
            raise ValueError("DASHSCOPE_API_KEY not configured")

        response = await self.client.embeddings.create(
            model=self.model,
            input=text,
        )
        return response.data[0].embedding

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """批量生成嵌入向量"""
        if not self.api_key:
            raise ValueError("DASHSCOPE_API_KEY not configured")

        # 批量处理，避免超过 API 限制
        results = []
        batch_size = 100

        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            response = await self.client.embeddings.create(
                model=self.model,
                input=batch,
            )
            results.extend([item.embedding for item in response.data])

        return results

    async def embed_experience(self, experience: Experience) -> list[float]:
        """为经验生成嵌入向量"""
        # 构建文本描述
        text = self._experience_to_text(experience)
        return await self.embed(text)

    def _experience_to_text(self, experience: Experience) -> str:
        """将经验转换为文本描述"""
        parts = [
            f"Task: {experience.task_description}",
            f"Category: {experience.task_category.value}",
            f"Success: {experience.success}",
            f"Evaluation Score: {experience.evaluation_score}",
            f"Completion Rate: {experience.completion_rate}",
        ]

        # 添加状态描述
        if experience.states:
            reasoning = " | ".join(s.content[:100] for s in experience.states[-3:])
            parts.append(f"Reasoning: {reasoning}")

        # 添加动作描述
        if experience.actions:
            actions = " | ".join(
                f"{a.name}({a.action_type.value})" for a in experience.actions[-5:]
            )
            parts.append(f"Actions: {actions}")

        return " | ".join(parts)

    async def similarity(self, text1: str, text2: str) -> float:
        """计算两个文本的余弦相似度"""
        import math

        emb1, emb2 = await asyncio.gather(
            self.embed(text1),
            self.embed(text2),
        )

        # 余弦相似度
        dot = sum(a * b for a, b in zip(emb1, emb2))
        norm1 = math.sqrt(sum(a * a for a in emb1))
        norm2 = math.sqrt(sum(b * b for b in emb2))

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot / (norm1 * norm2)

    async def find_similar(
        self,
        query: str,
        experiences: list[Experience],
        top_k: int = 5,
    ) -> list[tuple[Experience, float]]:
        """查找最相似的经验"""
        query_emb = await self.embed(query)

        # 过滤已有嵌入的经验
        with_embeddings = [e for e in experiences if e.embedding]

        if not with_embeddings:
            return []

        # 计算相似度
        similarities = []
        for exp in with_embeddings:
            sim = self._cosine_similarity(query_emb, exp.embedding)
            similarities.append((exp, sim))

        # 排序返回 top_k
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]

    def _cosine_similarity(self, a: list[float], b: list[float]) -> float:
        """计算余弦相似度"""
        import math

        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(y * y for y in b))

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return dot / (norm_a * norm_b)

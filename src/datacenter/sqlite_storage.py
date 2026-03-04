"""
SQLite Storage with Vector Search Support
SQLite 存储 + 向量检索
"""

import sqlite3
import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import numpy as np


@dataclass
class VectorRecord:
    """向量记录"""
    id: int
    content: str
    embedding: List[float]
    metadata: Dict[str, Any]


class SQLiteStorage:
    """SQLite 存储 + 向量检索"""

    def __init__(self, db_path: str = ".young/data.db"):
        self.db_path = db_path
        self._ensure_dir()
        self._init_db()

    def _ensure_dir(self):
        """确保目录存在"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

    def _init_db(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Traces 表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS traces (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                agent_name TEXT,
                task TEXT,
                result TEXT,
                duration_ms INTEGER,
                status TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Evaluations 表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS evaluations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                metric TEXT NOT NULL,
                score REAL NOT NULL,
                details TEXT,
                evaluator TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Capsules 表 (Evolver)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS capsules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                capsule_id TEXT UNIQUE NOT NULL,
                gene_id TEXT,
                trigger TEXT,
                summary TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Memory 表 (向量存储)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                embedding BLOB,
                namespace TEXT,
                tags TEXT,
                importance REAL DEFAULT 0.5,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 创建索引
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_traces_session ON traces(session_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_memory_namespace ON memory(namespace)")

        conn.commit()
        conn.close()

    # ========== Traces ==========

    def add_trace(
        self,
        session_id: str,
        agent_name: str,
        task: str,
        result: str,
        duration_ms: int = 0,
        status: str = "completed",
    ):
        """添加 trace"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO traces (session_id, agent_name, task, result, duration_ms, status) VALUES (?, ?, ?, ?, ?, ?)",
            (session_id, agent_name, task, result[:1000], duration_ms, status),
        )

        conn.commit()
        trace_id = cursor.lastrowid
        conn.close()
        return trace_id

    def get_traces(self, session_id: str = None, limit: int = 100) -> List[Dict]:
        """获取 traces"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        if session_id:
            cursor.execute(
                "SELECT * FROM traces WHERE session_id = ? ORDER BY created_at DESC LIMIT ?",
                (session_id, limit),
            )
        else:
            cursor.execute(
                "SELECT * FROM traces ORDER BY created_at DESC LIMIT ?", (limit,)
            )

        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    # ========== Evaluations ==========

    def add_evaluation(
        self,
        session_id: str,
        metric: str,
        score: float,
        details: Dict = None,
        evaluator: str = "default",
    ):
        """添加评估"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO evaluations (session_id, metric, score, details, evaluator) VALUES (?, ?, ?, ?, ?)",
            (session_id, metric, score, json.dumps(details) if details else "{}", evaluator),
        )

        conn.commit()
        eval_id = cursor.lastrowid
        conn.close()
        return eval_id

    def get_evaluations(self, session_id: str = None, limit: int = 100) -> List[Dict]:
        """获取 evaluations"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        if session_id:
            cursor.execute(
                "SELECT * FROM evaluations WHERE session_id = ? ORDER BY created_at DESC LIMIT ?",
                (session_id, limit),
            )
        else:
            cursor.execute(
                "SELECT * FROM evaluations ORDER BY created_at DESC LIMIT ?", (limit,)
            )

        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    # ========== Memory (向量存储) ==========

    def add_memory(
        self,
        content: str,
        embedding: List[float] = None,
        namespace: str = "default",
        tags: List[str] = None,
        importance: float = 0.5,
    ):
        """添加记忆"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 序列化 embedding
        embedding_blob = None
        if embedding:
            import numpy as np
            embedding_blob = np.array(embedding).tobytes()

        cursor.execute(
            "INSERT INTO memory (content, embedding, namespace, tags, importance) VALUES (?, ?, ?, ?, ?)",
            (content, embedding_blob, namespace, json.dumps(tags) if tags else "[]", importance),
        )

        conn.commit()
        memory_id = cursor.lastrowid
        conn.close()
        return memory_id

    def search_memory(
        self,
        query: str = None,
        embedding: List[float] = None,
        namespace: str = None,
        limit: int = 5,
    ) -> List[Dict]:
        """搜索记忆"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # 基础查询
        sql = "SELECT * FROM memory WHERE 1=1"
        params = []

        if namespace:
            sql += " AND namespace = ?"
            params.append(namespace)

        sql += " ORDER BY importance DESC, created_at DESC LIMIT ?"
        params.append(limit)

        cursor.execute(sql, params)
        rows = cursor.fetchall()
        conn.close()

        results = [dict(row) for row in rows]

        # 如果有 embedding，计算相似度
        if embedding and results:
            import numpy as np

            query_vec = np.array(embedding)
            for r in results:
                if r["embedding"]:
                    emb = np.frombuffer(r["embedding"])
                    # 简单余弦相似度
                    similarity = np.dot(query_vec, emb) / (
                        np.linalg.norm(query_vec) * np.linalg.norm(emb) + 1e-8
                    )
                    r["similarity"] = float(similarity)

            # 按相似度排序
            results.sort(key=lambda x: x.get("similarity", 0), reverse=True)

        return results

    # ========== Capsules ==========

    def add_capsule(self, capsule_id: str, gene_id: str, trigger: str, summary: str):
        """添加 capsule"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            "INSERT OR REPLACE INTO capsules (capsule_id, gene_id, trigger, summary) VALUES (?, ?, ?, ?)",
            (capsule_id, gene_id, trigger, summary),
        )

        conn.commit()
        conn.close()

    def get_capsules(self, limit: int = 100) -> List[Dict]:
        """获取 capsules"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM capsules ORDER BY created_at DESC LIMIT ?", (limit,)
        )

        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]


class EmbeddingClient:
    """Embedding API 客户端 - 支持多种模型"""

    def __init__(self, provider: str = "qwen"):
        self.provider = provider
        self.api_key = os.getenv("OPENAI_API_KEY") or os.getenv("DASHSCOPE_API_KEY")

    def embed(self, texts: List[str]) -> List[List[float]]:
        """获取 embedding"""
        if not texts:
            return []

        if self.provider == "qwen":
            return self._embed_qwen(texts)
        elif self.provider == "openai":
            return self._embed_openai(texts)
        else:
            # 返回随机向量作为占位
            return [self._random_embedding() for _ in texts]

    def _embed_qwen(self, texts: List[str]) -> List[List[float]]:
        """使用通义千问 API"""
        try:
            import httpx

            url = "https://dashscope.aliyuncs.com/compatible-mode/v1/embeddings"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            payload = {
                "model": "text-embedding-v3",
                "input": texts,
            }

            response = httpx.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()

            return [item["embedding"] for item in data["data"]]

        except Exception as e:
            print(f"[Warning] Embedding API failed: {e}")
            return [self._random_embedding() for _ in texts]

    def _embed_openai(self, texts: List[str]) -> List[List[float]]:
        """使用 OpenAI API"""
        try:
            import httpx

            url = "https://api.openai.com/v1/embeddings"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            payload = {
                "model": "text-embedding-3-small",
                "input": texts,
            }

            response = httpx.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()

            return [item["embedding"] for item in data["data"]]

        except Exception as e:
            print(f"[Warning] Embedding API failed: {e}")
            return [self._random_embedding() for _ in texts]

    def _random_embedding(self, dim: int = 1536) -> List[float]:
        """随机 embedding (占位)"""
        import numpy as np

        vec = np.random.randn(dim)
        vec = vec / np.linalg.norm(vec)
        return vec.tolist()

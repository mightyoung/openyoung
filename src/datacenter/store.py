"""
DataStore - 统一数据访问入口
基于 SQLAlchemy 实现统一的数据访问层
"""

import json
import sqlite3
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

# Blinker for events
from blinker import signal

# SQLAlchemy
from sqlalchemy import Column, DateTime, Index, Integer, String, Text, create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

# 事件信号
checkpoint_saved = signal("checkpoint.saved")
run_started = signal("run.started")
run_completed = signal("run.completed")
workspace_created = signal("workspace.created")

Base = declarative_base()


# ========== SQLAlchemy Models ==========


class EntityType(str, Enum):
    """实体类型"""

    AGENT = "agent"
    RUN = "run"
    CHECKPOINT = "checkpoint"
    WORKSPACE = "workspace"
    USER = "user"


class Entity(Base):
    """统一实体表"""

    __tablename__ = "entities"

    id = Column(String, primary_key=True)
    entity_type = Column(String, nullable=False, index=True)
    version = Column(Integer, default=1)

    # JSON 数据
    data = Column(Text, nullable=False)

    # 元数据 (重命名为 extra_data 避免 SQLAlchemy 冲突)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    extra_data = Column(Text, default="{}")

    # 索引
    __table_args__ = (
        Index("idx_entity_type", "entity_type"),
        Index("idx_entity_updated", "updated_at"),
    )


class Version(Base):
    """版本历史表"""

    __tablename__ = "versions"

    id = Column(String, primary_key=True)
    entity_type = Column(String, nullable=False)
    entity_id = Column(String, nullable=False)
    version = Column(Integer, nullable=False)
    parent_id = Column(String)

    # 数据
    data = Column(Text, nullable=False)
    message = Column(Text, default="")

    created_at = Column(DateTime, default=datetime.now)

    __table_args__ = (Index("idx_version_entity", "entity_type", "entity_id"),)


# ========== DataStore ==========


class DataStore:
    """统一数据访问入口"""

    def __init__(self, data_dir: str = ".young"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.db_path = self.data_dir / "datastore.db"
        self.engine = create_engine(f"sqlite:///{self.db_path}")
        self.SessionLocal = sessionmaker(bind=self.engine)

        # 初始化表
        Base.metadata.create_all(self.engine)

    def _get_session(self) -> Session:
        """获取数据库会话"""
        return self.SessionLocal()

    def _serialize(self, data: Any) -> str:
        """序列化数据为 JSON"""
        if isinstance(data, dict):
            return json.dumps(data, ensure_ascii=False, default=str)
        return str(data)

    def _deserialize(self, data: str) -> Any:
        """反序列化 JSON"""
        try:
            return json.loads(data)
        except:
            return data

    # ===== Agent 操作 =====

    def save_agent(self, agent_id: str, data: dict) -> str:
        """保存 Agent"""
        entity = Entity(
            id=agent_id,
            entity_type=EntityType.AGENT.value,
            data=self._serialize(data),
            created_at=datetime.now(),
        )

        with self._get_session() as session:
            existing = session.query(Entity).filter_by(id=agent_id).first()
            if existing:
                existing.data = entity.data
                existing.updated_at = datetime.now()
            else:
                session.add(entity)
            session.commit()

        return agent_id

    def get_agent(self, agent_id: str) -> dict | None:
        """获取 Agent"""
        with self._get_session() as session:
            entity = (
                session.query(Entity)
                .filter_by(id=agent_id, entity_type=EntityType.AGENT.value)
                .first()
            )
            return self._deserialize(entity.data) if entity else None

    def list_agents(self, limit: int = 100) -> list[dict]:
        """列出所有 Agents"""
        with self._get_session() as session:
            entities = (
                session.query(Entity)
                .filter_by(entity_type=EntityType.AGENT.value)
                .order_by(Entity.updated_at.desc())
                .limit(limit)
                .all()
            )
            return [{"id": e.id, **self._deserialize(e.data)} for e in entities]

    def delete_agent(self, agent_id: str) -> bool:
        """删除 Agent"""
        with self._get_session() as session:
            entity = (
                session.query(Entity)
                .filter_by(id=agent_id, entity_type=EntityType.AGENT.value)
                .first()
            )
            if entity:
                session.delete(entity)
                session.commit()
                return True
            return False

    # ===== Run 操作 =====

    def save_run(self, run_id: str, data: dict) -> str:
        """保存运行记录"""
        entity = Entity(
            id=run_id,
            entity_type=EntityType.RUN.value,
            data=self._serialize(data),
            created_at=datetime.now(),
        )

        with self._get_session() as session:
            existing = session.query(Entity).filter_by(id=run_id).first()
            if existing:
                existing.data = entity.data
                existing.updated_at = datetime.now()
            else:
                session.add(entity)
            session.commit()

        # 发送事件
        run_completed.send(self, run_id=run_id, data=data)

        return run_id

    def get_run(self, run_id: str) -> dict | None:
        """获取运行记录"""
        with self._get_session() as session:
            entity = (
                session.query(Entity).filter_by(id=run_id, entity_type=EntityType.RUN.value).first()
            )
            return self._deserialize(entity.data) if entity else None

    def list_runs(self, agent_id: str = None, limit: int = 100) -> list[dict]:
        """列出运行记录"""
        with self._get_session() as session:
            query = session.query(Entity).filter_by(entity_type=EntityType.RUN.value)
            if agent_id:
                # 通过 metadata 过滤
                entities = query.all()
                results = []
                for e in entities:
                    data = self._deserialize(e.data)
                    if data.get("agent_id") == agent_id:
                        results.append({"id": e.id, **data})
                return results[:limit]
            else:
                entities = query.order_by(Entity.updated_at.desc()).limit(limit).all()
                return [{"id": e.id, **self._deserialize(e.data)} for e in entities]

    # ===== Checkpoint 操作 =====

    def save_checkpoint(self, checkpoint_id: str, data: dict) -> str:
        """保存 Checkpoint"""
        entity = Entity(
            id=checkpoint_id,
            entity_type=EntityType.CHECKPOINT.value,
            data=self._serialize(data),
            created_at=datetime.now(),
        )

        with self._get_session() as session:
            session.add(entity)
            session.commit()

        # 发送事件
        checkpoint_saved.send(self, checkpoint_id=checkpoint_id, data=data)

        return checkpoint_id

    def get_checkpoint(self, checkpoint_id: str) -> dict | None:
        """获取 Checkpoint"""
        with self._get_session() as session:
            entity = (
                session.query(Entity)
                .filter_by(id=checkpoint_id, entity_type=EntityType.CHECKPOINT.value)
                .first()
            )
            return self._deserialize(entity.data) if entity else None

    def list_checkpoints(self, session_id: str = None, limit: int = 10) -> list[dict]:
        """列出 Checkpoints"""
        with self._get_session() as session:
            query = session.query(Entity).filter_by(entity_type=EntityType.CHECKPOINT.value)

            if session_id:
                entities = query.all()
                results = []
                for e in entities:
                    data = self._deserialize(e.data)
                    if data.get("session_id") == session_id:
                        results.append({"id": e.id, **data})
                return results[:limit]
            else:
                entities = query.order_by(Entity.created_at.desc()).limit(limit).all()
                return [{"id": e.id, **self._deserialize(e.data)} for e in entities]

    # ===== Workspace 操作 =====

    def save_workspace(self, workspace_id: str, data: dict) -> str:
        """保存 Workspace"""
        entity = Entity(
            id=workspace_id,
            entity_type=EntityType.WORKSPACE.value,
            data=self._serialize(data),
            created_at=datetime.now(),
        )

        with self._get_session() as session:
            existing = session.query(Entity).filter_by(id=workspace_id).first()
            if existing:
                existing.data = entity.data
                existing.updated_at = datetime.now()
            else:
                session.add(entity)
            session.commit()

        # 发送事件
        workspace_created.send(self, workspace_id=workspace_id, data=data)

        return workspace_id

    def get_workspace(self, workspace_id: str) -> dict | None:
        """获取 Workspace"""
        with self._get_session() as session:
            entity = (
                session.query(Entity)
                .filter_by(id=workspace_id, entity_type=EntityType.WORKSPACE.value)
                .first()
            )
            return self._deserialize(entity.data) if entity else None

    # ===== 事务操作 =====

    def save_with_transaction(self, operations: list[dict]) -> bool:
        """原子性执行多个操作"""
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("BEGIN IMMEDIATE")
            cursor = conn.cursor()

            for op in operations:
                entity_type = op.get("entity_type")
                entity_id = op.get("id")
                data = self._serialize(op.get("data"))

                cursor.execute(
                    """
                    INSERT OR REPLACE INTO entities (id, entity_type, data, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                """,
                    (
                        entity_id,
                        entity_type,
                        data,
                        datetime.now().isoformat(),
                        datetime.now().isoformat(),
                    ),
                )

            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    # ===== 版本控制 =====

    def save_version(self, entity_type: str, entity_id: str, data: dict, message: str = "") -> str:
        """保存版本"""
        # 获取当前版本号
        with self._get_session() as session:
            latest = (
                session.query(Version)
                .filter_by(entity_type=entity_type, entity_id=entity_id)
                .order_by(Version.version.desc())
                .first()
            )

            version = (latest.version + 1) if latest else 1
            version_id = f"{entity_id}_v{version}"

            ver = Version(
                id=version_id,
                entity_type=entity_type,
                entity_id=entity_id,
                version=version,
                parent_id=latest.id if latest else "",
                data=self._serialize(data),
                message=message,
                created_at=datetime.now(),
            )

            session.add(ver)
            session.commit()

            return version_id

    def get_version(self, version_id: str) -> dict | None:
        """获取版本"""
        with self._get_session() as session:
            ver = session.query(Version).filter_by(id=version_id).first()
            return self._deserialize(ver.data) if ver else None

    def list_versions(self, entity_type: str, entity_id: str) -> list[dict]:
        """列出版本历史"""
        with self._get_session() as session:
            versions = (
                session.query(Version)
                .filter_by(entity_type=entity_type, entity_id=entity_id)
                .order_by(Version.version.desc())
                .all()
            )

            return [
                {
                    "id": v.id,
                    "version": v.version,
                    "parent_id": v.parent_id,
                    "message": v.message,
                    "created_at": v.created_at.isoformat(),
                    **self._deserialize(v.data),
                }
                for v in versions
            ]

    # ===== 统计 =====

    def get_stats(self) -> dict:
        """获取统计信息"""
        with self._get_session() as session:
            stats = {}
            for et in EntityType:
                count = session.query(Entity).filter_by(entity_type=et.value).count()
                stats[et.value] = count
            return stats


# ========== 便捷函数 ==========


def get_data_store(data_dir: str = ".young") -> DataStore:
    """获取 DataStore 实例"""
    return DataStore(data_dir)

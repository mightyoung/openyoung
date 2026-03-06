"""
DataWarehouse - 数据资产化管理
将运行数据转化为可分析的数据资产
"""

import sqlite3
import json
import csv
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field


@dataclass
class DatasetConfig:
    """数据集配置"""
    name: str
    description: str = ""
    tags: List[str] = field(default_factory=list)
    version: str = "1.0.0"
    created_at: datetime = field(default_factory=datetime.now)


class DataWarehouse:
    """数据仓库 - 数据资产化管理"""

    def __init__(self, data_dir: str = ".young"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # 数据仓库路径
        self.warehouse_dir = self.data_dir / "warehouse"
        self.warehouse_dir.mkdir(parents=True, exist_ok=True)

        # 数据库
        self.db_path = self.data_dir / "warehouse.db"
        self._init_db()

    def _init_db(self):
        """初始化数据仓库数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 数据集表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS datasets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                description TEXT,
                tags TEXT,
                version TEXT,
                record_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP
            )
        """)

        # 导出历史表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS exports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dataset_name TEXT,
                format TEXT,
                file_path TEXT,
                record_count INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 使用统计表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usage_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                agent_id TEXT,
                user_id TEXT,
                run_count INTEGER DEFAULT 0,
                token_count INTEGER DEFAULT 0,
                cost_usd REAL DEFAULT 0,
                avg_duration_ms INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        conn.close()

    def register_dataset(self, config: DatasetConfig) -> bool:
        """注册数据集"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO datasets (name, description, tags, version)
                VALUES (?, ?, ?, ?)
            """, (config.name, config.description, json.dumps(config.tags), config.version))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()

    def update_dataset_stats(self, name: str, record_count: int):
        """更新数据集统计"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE datasets
            SET record_count = ?, updated_at = ?
            WHERE name = ?
        """, (record_count, datetime.now().isoformat(), name))

        conn.commit()
        conn.close()

    def create_dataset_from_traces(self, name: str, description: str = "", tags: List[str] = None) -> int:
        """从 traces 创建数据集"""
        # 注册数据集
        config = DatasetConfig(name=name, description=description, tags=tags or [])
        self.register_dataset(config)

        # 从 traces.db 读取数据
        traces_db = self.data_dir / "traces.db"
        if not traces_db.exists():
            return 0

        conn = sqlite3.connect(str(traces_db))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM traces")
        records = cursor.fetchall()
        conn.close()

        # 导出到数据集文件
        dataset_file = self.warehouse_dir / f"{name}.json"
        data = [dict(row) for row in records]

        with open(dataset_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        # 更新统计
        self.update_dataset_stats(name, len(data))

        return len(data)

    def export_dataset(
        self,
        name: str,
        format: str = "json",
        filters: Dict = None
    ) -> Optional[str]:
        """导出数据集"""
        dataset_file = self.warehouse_dir / f"{name}.{format}"
        json_file = self.warehouse_dir / f"{name}.json"

        if not json_file.exists():
            return None

        # 读取数据
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 应用过滤
        if filters:
            filtered = []
            for record in data:
                match = True
                for key, value in filters.items():
                    if record.get(key) != value:
                        match = False
                        break
                if match:
                    filtered.append(record)
            data = filtered

        # 导出
        export_path = self.warehouse_dir / f"{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format}"

        if format == "json":
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

        elif format == "csv":
            if not data:
                return None
            keys = data[0].keys()
            with open(export_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=keys)
                writer.writeheader()
                writer.writerows(data)

        # 记录导出历史
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO exports (dataset_name, format, file_path, record_count)
            VALUES (?, ?, ?, ?)
        """, (name, format, str(export_path), len(data)))
        conn.commit()
        conn.close()

        return str(export_path)

    def get_usage_stats(
        self,
        agent_id: str = None,
        user_id: str = None,
        days: int = 30
    ) -> List[Dict]:
        """获取使用统计"""
        traces_db = self.data_dir / "traces.db"
        if not traces_db.exists():
            return []

        conn = sqlite3.connect(str(traces_db))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # 计算日期范围
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

        sql = """
            SELECT
                date(start_time) as date,
                agent_name,
                COUNT(*) as run_count,
                SUM(total_tokens) as token_count,
                SUM(cost_usd) as cost_usd,
                AVG(duration_ms) as avg_duration
            FROM traces
            WHERE start_time >= ?
        """
        params = [start_date]

        if agent_id:
            sql += " AND agent_name = ?"
            params.append(agent_id)

        if user_id:
            sql += " AND user_id = ?"
            params.append(user_id)

        sql += " GROUP BY date(start_time), agent_name ORDER BY date DESC"

        cursor.execute(sql, params)
        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def get_agent_leaderboard(self, limit: int = 10, days: int = 30) -> List[Dict]:
        """获取 Agent 排行榜"""
        traces_db = self.data_dir / "traces.db"
        if not traces_db.exists():
            return []

        conn = sqlite3.connect(str(traces_db))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

        cursor.execute("""
            SELECT
                agent_name,
                COUNT(*) as total_runs,
                SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success_count,
                SUM(total_tokens) as total_tokens,
                SUM(cost_usd) as total_cost,
                AVG(duration_ms) as avg_duration
            FROM traces
            WHERE start_time >= ?
            GROUP BY agent_name
            ORDER BY total_runs DESC
            LIMIT ?
        """, (start_date, limit))

        rows = cursor.fetchall()
        conn.close()

        result = []
        for row in rows:
            d = dict(row)
            d['success_rate'] = d['success_count'] / d['total_runs'] if d['total_runs'] > 0 else 0
            result.append(d)

        return result

    def get_cost_breakdown(self, days: int = 30) -> Dict:
        """获取成本分解"""
        traces_db = self.data_dir / "traces.db"
        if not traces_db.exists():
            return {}

        conn = sqlite3.connect(str(traces_db))
        cursor = conn.cursor()

        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

        # 按 Agent 统计
        cursor.execute("""
            SELECT
                agent_name,
                SUM(cost_usd) as cost
            FROM traces
            WHERE start_time >= ?
            GROUP BY agent_name
            ORDER BY cost DESC
        """, (start_date,))

        by_agent = {row[0]: row[1] for row in cursor.fetchall()}

        # 总成本
        cursor.execute("""
            SELECT SUM(cost_usd) FROM traces WHERE start_time >= ?
        """, (start_date,))
        total = cursor.fetchone()[0] or 0

        conn.close()

        return {
            "total_cost": total,
            "by_agent": by_agent,
            "period_days": days
        }

    def list_datasets(self) -> List[Dict]:
        """列出所有数据集"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM datasets ORDER BY created_at DESC")
        rows = cursor.fetchall()
        conn.close()

        result = []
        for row in rows:
            d = dict(row)
            d['tags'] = json.loads(d['tags']) if d['tags'] else []
            result.append(d)

        return result

    def get_export_history(self, dataset_name: str = None) -> List[Dict]:
        """获取导出历史"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        if dataset_name:
            cursor.execute("""
                SELECT * FROM exports
                WHERE dataset_name = ?
                ORDER BY created_at DESC
            """, (dataset_name,))
        else:
            cursor.execute("SELECT * FROM exports ORDER BY created_at DESC")

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]


# ========== 便捷函数 ==========

def get_data_warehouse(data_dir: str = ".young") -> DataWarehouse:
    """获取数据仓库实例"""
    return DataWarehouse(data_dir)

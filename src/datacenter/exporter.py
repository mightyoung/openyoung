"""
DataExporter - 数据导出
支持多种格式导出，带授权信息
统一数据源：只从 runs.db 读取
"""

import csv
import json
import sqlite3
from datetime import datetime
from pathlib import Path

from .base_storage import BaseStorage


class DataExporter(BaseStorage):
    """数据导出器"""

    def __init__(self, data_dir: str = ".young"):
        self.data_dir = Path(data_dir)
        self._db_path = str(self.data_dir / "runs.db")

    @property
    def db_path(self) -> str:
        return self._db_path

    def _ensure_db_exists(self) -> bool:
        return Path(self._db_path).exists()

    def _init_db(self) -> None:
        """Exporter 不需要建表"""
        pass

    def export_runs(self, output_path: str, format: str = "json", agent_id: str = None) -> bool:
        """导出运行记录（只从 runs.db 读取）"""
        db_path = self.data_dir / "runs.db"
        if not db_path.exists():
            print(f"Database not found: {db_path}")
            return False

        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            query = "SELECT * FROM runs"
            if agent_id:
                query += " WHERE agent_id = ?"
                cursor.execute(query, (agent_id,))
            else:
                cursor.execute(query)

            rows = cursor.fetchall()
            results = [dict(row) for row in rows]
        finally:
            conn.close()

        if not results:
            print("No runs to export")
            return False

        return self._write_output(output_path, format, results)

    def export_steps(self, output_path: str, format: str = "json", run_id: str = None) -> bool:
        """导出步骤记录"""
        db_path = self.data_dir / "steps.db"
        if not db_path.exists():
            print(f"Database not found: {db_path}")
            return False

        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            query = "SELECT * FROM steps"
            if run_id:
                query += " WHERE run_id = ?"
                cursor.execute(query, (run_id,))
            else:
                cursor.execute(query)

            rows = cursor.fetchall()
            results = [dict(row) for row in rows]
        finally:
            conn.close()

        if not results:
            print("No steps to export")
            return False

        return self._write_output(output_path, format, results)

    def export_agents(self, output_path: str, format: str = "json") -> bool:
        """导出 Agent 数据（从 runs.db 查询唯一 agent_id）"""
        db_path = self.data_dir / "runs.db"
        if not db_path.exists():
            print(f"Database not found: {db_path}")
            return False

        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            # 从 runs 表提取唯一的 agent 信息
            cursor.execute("""
                SELECT DISTINCT agent_id, MIN(started_at) as first_run,
                       COUNT(*) as total_runs,
                       SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success_runs
                FROM runs
                GROUP BY agent_id
            """)

            rows = cursor.fetchall()
            results = []
            for row in rows:
                results.append({
                    "agent_id": row["agent_id"],
                    "first_run": row["first_run"],
                    "total_runs": row["total_runs"],
                    "success_runs": row["success_runs"]
                })
        finally:
            conn.close()

        if not results:
            print("No agents to export")
            return False

        return self._write_output(output_path, format, results)

    def _write_output(self, output_path: str, format: str, results: list[dict]) -> bool:
        """写入输出文件"""
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)

        if format == "json":
            with open(output, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        elif format == "csv":
            if results:
                # 展平嵌套字典
                flat_data = []
                for r in results:
                    flat = {}
                    for k, v in r.items():
                        if isinstance(v, dict):
                            flat.update({f"{k}_{sk}": sv for sk, sv in v.items()})
                        else:
                            flat[k] = v
                    flat_data.append(flat)

                if flat_data:
                    with open(output, "w", encoding="utf-8", newline="") as f:
                        writer = csv.DictWriter(f, fieldnames=flat_data[0].keys(), extrasaction='ignore')
                        writer.writeheader()
                        writer.writerows(flat_data)

        print(f"Exported {len(results)} records to {output_path}")
        return True

    def export_with_license(
        self,
        output_path: str,
        data_type: str,
        license: dict
    ) -> bool:
        """带授权信息导出"""
        # 先导出数据
        if data_type == "runs":
            success = self.export_runs(output_path)
        elif data_type == "agents":
            success = self.export_agents(output_path)
        elif data_type == "steps":
            success = self.export_steps(output_path)
        else:
            print(f"Unsupported data type: {data_type}")
            return False

        if not success:
            return False

        # 添加授权信息到元数据文件
        license_path = Path(output_path).with_suffix(".license.json")
        license_info = {
            "data_file": str(output_path),
            "data_type": data_type,
            "license": license,
            "exported_at": datetime.now().isoformat()
        }

        with open(license_path, "w", encoding="utf-8") as f:
            json.dump(license_info, f, indent=2, ensure_ascii=False)

        print(f"License file created: {license_path}")
        return True

    def export_full(self, output_dir: str) -> dict[str, str]:
        """导出所有数据"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        exported = {}

        # 导出 runs
        runs_file = output_path / "runs.json"
        if self.export_runs(str(runs_file)):
            exported["runs"] = str(runs_file)

        # 导出 agents（从 runs 提取）
        agents_file = output_path / "agents.json"
        if self.export_agents(str(agents_file)):
            exported["agents"] = str(agents_file)

        # 导出 steps（如果存在）
        steps_file = output_path / "steps.json"
        if self.export_steps(str(steps_file)):
            exported["steps"] = str(steps_file)

        # 导出元数据
        metadata = {
            "exported_at": datetime.now().isoformat(),
            "files": list(exported.keys())
        }
        meta_file = output_path / "metadata.json"
        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)
        exported["metadata"] = str(meta_file)

        return exported


# ========== 便捷函数 ==========

def get_data_exporter(data_dir: str = ".young") -> DataExporter:
    """获取数据导出器"""
    return DataExporter(data_dir)

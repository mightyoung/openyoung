"""
Tenant DataStore - 租户物理隔离数据存储
每个租户有独立的数据目录和数据库
"""

import shutil
from datetime import datetime
from pathlib import Path

from .store import DataStore


class TenantDataStore:
    """租户专属数据存储 - 物理隔离"""

    def __init__(self, tenant_id: str, base_dir: str = ".young"):
        self.tenant_id = tenant_id

        # 物理隔离目录
        self.data_dir = Path(base_dir) / "tenants" / tenant_id
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # 每个租户独立数据库
        self.db_path = self.data_dir / "data.db"

        # 使用 DataStore
        self.store = DataStore(str(self.data_dir))

    def get_data_dir(self) -> Path:
        """获取租户数据目录"""
        return self.data_dir

    def export_data(self, export_path: str) -> bool:
        """导出租户所有数据"""
        import json

        export_dir = Path(export_path)
        export_dir.mkdir(parents=True, exist_ok=True)

        # 导出所有 agents
        agents = self.store.list_agents(limit=10000)
        with open(export_dir / "agents.json", "w") as f:
            json.dump(agents, f, indent=2, ensure_ascii=False)

        # 导出所有 runs
        runs = self.store.list_runs(limit=10000)
        with open(export_dir / "runs.json", "w") as f:
            json.dump(runs, f, indent=2, ensure_ascii=False)

        # 导出元数据
        metadata = {
            "tenant_id": self.tenant_id,
            "exported_at": datetime.now().isoformat(),
            "agent_count": len(agents),
            "run_count": len(runs),
        }
        with open(export_dir / "metadata.json", "w") as f:
            json.dump(metadata, f, indent=2)

        return True

    def import_data(self, import_path: str) -> int:
        """导入数据"""
        import json

        imported = 0
        import_dir = Path(import_path)

        # 导入 agents
        agents_file = import_dir / "agents.json"
        if agents_file.exists():
            with open(agents_file) as f:
                agents = json.load(f)
                for agent in agents:
                    self.store.save_agent(agent["id"], agent)
                    imported += 1

        # 导入 runs
        runs_file = import_dir / "runs.json"
        if runs_file.exists():
            with open(runs_file) as f:
                runs = json.load(f)
                for run in runs:
                    self.store.save_run(run["id"], run)
                    imported += 1

        return imported

    def delete_all_data(self) -> bool:
        """删除租户所有数据"""
        if self.data_dir.exists():
            shutil.rmtree(self.data_dir)
        return True


class TenantManager:
    """租户管理器"""

    def __init__(self, base_dir: str = ".young"):
        self.base_dir = Path(base_dir)
        self.tenants_dir = self.base_dir / "tenants"
        self.tenants_dir.mkdir(parents=True, exist_ok=True)

        # 租户元数据存储
        self.meta_path = self.tenants_dir / "tenants.json"
        self._load_tenants()

    def _load_tenants(self):
        """加载租户列表"""
        import json

        if self.meta_path.exists():
            with open(self.meta_path) as f:
                self._tenants = json.load(f)
        else:
            self._tenants = {}

    def _save_tenants(self):
        """保存租户列表"""
        import json

        with open(self.meta_path, "w") as f:
            json.dump(self._tenants, f, indent=2)

    def create_tenant(self, tenant_id: str, name: str = "", **kwargs) -> TenantDataStore:
        """创建租户"""
        if tenant_id in self._tenants:
            return self.get_tenant(tenant_id)

        # 创建租户目录
        tenant_dir = self.tenants_dir / tenant_id
        tenant_dir.mkdir(parents=True, exist_ok=True)

        # 保存元数据
        self._tenants[tenant_id] = {
            "name": name or tenant_id,
            "created_at": datetime.now().isoformat(),
            "status": "active",
            **kwargs,
        }
        self._save_tenants()

        return TenantDataStore(tenant_id, str(self.base_dir))

    def get_tenant(self, tenant_id: str) -> TenantDataStore | None:
        """获取租户"""
        if tenant_id not in self._tenants:
            return None
        return TenantDataStore(tenant_id, str(self.base_dir))

    def list_tenants(self) -> list[dict]:
        """列出租户"""
        return [{"tenant_id": tid, **info} for tid, info in self._tenants.items()]

    def delete_tenant(self, tenant_id: str) -> bool:
        """删除租户"""
        if tenant_id not in self._tenants:
            return False

        # 删除数据目录
        tenant_dir = self.tenants_dir / tenant_id
        if tenant_dir.exists():
            shutil.rmtree(tenant_dir)

        # 删除元数据
        del self._tenants[tenant_id]
        self._save_tenants()

        return True

    def suspend_tenant(self, tenant_id: str) -> bool:
        """暂停租户"""
        if tenant_id in self._tenants:
            self._tenants[tenant_id]["status"] = "suspended"
            self._save_tenants()
            return True
        return False

    def activate_tenant(self, tenant_id: str) -> bool:
        """激活租户"""
        if tenant_id in self._tenants:
            self._tenants[tenant_id]["status"] = "active"
            self._save_tenants()
            return True
        return False


# ========== 便捷函数 ==========


def get_tenant_manager(base_dir: str = ".young") -> TenantManager:
    """获取租户管理器"""
    return TenantManager(base_dir)


def get_tenant_store(tenant_id: str, base_dir: str = ".young") -> TenantDataStore:
    """获取租户数据存储"""
    return TenantDataStore(tenant_id, base_dir)

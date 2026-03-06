# 数据系统测试评估计划

## 1. 测试范围

### 1.1 测试对象

| 模块 | 文件 | 功能 |
|------|------|------|
| 数据模型 | `src/datacenter/models.py` | AgentRunData, UserData, AgentData, EvaluationData |
| 工作空间 | `src/datacenter/workspace.py` | WorkspaceManager, 隔离管理 |
| 隔离控制 | `src/datacenter/isolation.py` | IsolationManager, 多级别隔离 |
| Checkpoint | `src/datacenter/datacenter.py` | CheckpointManager, 状态持久化 |
| Trace | `src/datacenter/datacenter.py` | TraceCollector, 追踪收集 |
| 数据仓库 | `src/datacenter/datawarehouse.py` | DataWarehouse, 数据资产化 |
| 追踪导出 | `src/datacenter/tracing.py` | OpenTelemetry, LangSmith |
| 企业功能 | `src/datacenter/enterprise.py` | 多租户, 权限, 审计 |

### 1.2 设计要求对照

| 设计要求 | 实现状态 | 测试策略 |
|----------|----------|----------|
| SQLite 持久化 | ✅ | 验证数据写入/读取 |
| Agent 工作空间隔离 | ✅ | 验证目录隔离 |
| Session/User/Agent 隔离 | ✅ | 验证数据隔离 |
| Checkpoint 状态恢复 | ✅ | 验证保存/加载 |
| 数据资产化 | ✅ | 验证导出功能 |
| OpenTelemetry 导出 | ✅ | 验证 OTLP 格式 |
| LangSmith 集成 | ✅ | 验证 API 调用 |
| 多租户支持 | ✅ | 验证租户隔离 |
| 权限控制 | ✅ | 验证权限检查 |
| 审计日志 | ✅ | 验证日志记录 |

---

## 2. 测试用例

### 2.1 数据模型测试

```python
# test_models.py
import pytest
from src.datacenter.models import (
    AgentRunData, UserData, AgentData, EvaluationData,
    IsolationLevel, RunStatus
)

def test_agent_run_data_creation():
    """测试 AgentRunData 创建"""
    run = AgentRunData(
        user_id="user-001",
        agent_id="agent-coder",
        session_id="session-001",
        status=RunStatus.SUCCESS,
        prompt_tokens=100,
        completion_tokens=50
    )
    assert run.run_id is not None
    assert run.status == RunStatus.SUCCESS

def test_agent_run_data_to_dict():
    """测试 AgentRunData 序列化"""
    run = AgentRunData(user_id="user-001", agent_id="agent-coder")
    d = run.to_dict()
    assert "run_id" in d
    assert "user_id" in d
    assert d["user_id"] == "user-001"

def test_isolation_level_enum():
    """测试隔离级别枚举"""
    assert IsolationLevel.SESSION.value == "session"
    assert IsolationLevel.USER.value == "user"
    assert IsolationLevel.AGENT.value == "agent"
    assert IsolationLevel.GLOBAL.value == "global"
```

### 2.2 工作空间测试

```python
# test_workspace.py
import pytest
import shutil
from pathlib import Path
from src.datacenter.workspace import (
    WorkspaceManager, WorkspaceQuota, WorkspaceStatus
)

TEST_ROOT = ".young/test_workspace_unit"

@pytest.fixture
def wm():
    wm = WorkspaceManager(TEST_ROOT)
    yield wm
    # Cleanup
    if Path(TEST_ROOT).exists():
        shutil.rmtree(TEST_ROOT)

def test_create_workspace(wm):
    """测试创建工作空间"""
    ws = wm.create_workspace("agent-001", user_id="user-001")
    assert ws.agent_id == "agent-001"
    assert ws.user_id == "user-001"
    assert ws.root_path.exists()

def test_workspace_directory_structure(wm):
    """测试工作空间目录结构"""
    ws = wm.create_workspace("agent-002")
    assert (ws.root_path / "memory").exists()
    assert (ws.root_path / "checkpoints").exists()
    assert (ws.root_path / "traces").exists()
    assert (ws.root_path / "output").exists()
    assert (ws.root_path / "config").exists()

def test_workspace_quota(wm):
    """测试工作空间配额"""
    quota = WorkspaceQuota(max_storage_mb=100, max_checkpoints=20)
    ws = wm.create_workspace("agent-003", quota=quota)
    assert ws.quota.max_storage_mb == 100
    assert ws.quota.max_checkpoints == 20

def test_workspace_archive(wm):
    """测试工作空间归档"""
    wm.create_workspace("agent-004")
    wm.archive_workspace("agent-004")
    ws = wm.get_workspace("agent-004")
    assert ws.status == WorkspaceStatus.ARCHIVED

def test_workspace_copy(wm):
    """测试工作空间复制"""
    ws1 = wm.create_workspace("agent-005")
    ws2 = wm.copy_workspace("agent-005", "agent-006")
    assert ws2.agent_id == "agent-006"
    assert ws2.root_path.exists()

def test_workspace_stats(wm):
    """测试工作空间统计"""
    wm.create_workspace("agent-007")
    wm.create_workspace("agent-008")
    stats = wm.get_all_stats()
    assert stats["total_agents"] == 2
```

### 2.3 隔离控制测试

```python
# test_isolation.py
import pytest
import shutil
from pathlib import Path
from src.datacenter.isolation import IsolationManager
from src.datacenter.models import IsolationLevel

TEST_ISOLATION = ".young/test_isolation_unit"

@pytest.fixture
def im():
    im = IsolationManager(TEST_ISOLATION)
    yield im
    if Path(TEST_ISOLATION).exists():
        shutil.rmtree(TEST_ISOLATION)

def test_session_isolation(im):
    """测试 Session 级别隔离"""
    path = im.create_isolation_dirs(
        level=IsolationLevel.SESSION,
        session_id="session-001"
    )
    assert "sessions/session-001" in str(path)

def test_user_isolation(im):
    """测试 User 级别隔离"""
    path = im.create_isolation_dirs(
        level=IsolationLevel.USER,
        user_id="user-001"
    )
    assert "users/user-001" in str(path)

def test_agent_isolation(im):
    """测试 Agent 级别隔离"""
    path = im.create_isolation_dirs(
        level=IsolationLevel.AGENT,
        agent_id="agent-coder"
    )
    assert "agents/agent-coder" in str(path)

def test_save_and_load_data(im):
    """测试隔离数据保存和加载"""
    im.save_data(
        key="context",
        data={"messages": ["hello", "world"]},
        level=IsolationLevel.SESSION,
        session_id="session-002"
    )
    data = im.load_data(
        key="context",
        level=IsolationLevel.SESSION,
        session_id="session-002"
    )
    assert data == {"messages": ["hello", "world"]}

def test_query_isolation_data(im):
    """测试隔离数据查询"""
    im.save_data("key1", "value1", IsolationLevel.SESSION, session_id="s1")
    im.save_data("key2", "value2", IsolationLevel.USER, user_id="u1")
    results = im.query_data(level=IsolationLevel.SESSION)
    assert len(results) >= 1
```

### 2.4 Checkpoint 测试

```python
# test_checkpoint.py
import pytest
import shutil
from pathlib import Path
from src.datacenter.datacenter import CheckpointManager

TEST_CP = ".young/test_cp_unit"

@pytest.fixture
def cm():
    cm = CheckpointManager(TEST_CP, f"{TEST_CP}.db")
    yield cm
    if Path(TEST_CP).exists():
        shutil.rmtree(TEST_CP)

def test_save_checkpoint(cm):
    """测试保存 checkpoint"""
    cp_id = cm.save_checkpoint(
        session_id="session-001",
        data={"state": "running", "progress": 50},
        agent_id="agent-001"
    )
    assert cp_id is not None
    assert "session-001" in cp_id

def test_load_checkpoint(cm):
    """测试加载 checkpoint"""
    cp_id = cm.save_checkpoint("s1", {"data": "test"}, "a1")
    cp = cm.load_checkpoint(cp_id)
    assert cp is not None
    assert cp.data["data"] == "test"

def test_get_latest_checkpoint(cm):
    """测试获取最新 checkpoint"""
    cm.save_checkpoint("s2", {"step": 1}, "a1")
    cm.save_checkpoint("s2", {"step": 2}, "a1")
    latest = cm.get_latest("s2")
    assert latest.data["step"] == 2

def test_checkpoint_persistence(cm):
    """测试 checkpoint 持久化"""
    cm.save_checkpoint("s3", {"persistent": True}, "a1")
    # 重新创建 manager
    cm2 = CheckpointManager(TEST_CP, f"{TEST_CP}.db")
    latest = cm2.get_latest("s3")
    assert latest is not None
    assert latest.data["persistent"] == True
```

### 2.5 数据仓库测试

```python
# test_datawarehouse.py
import pytest
import shutil
from pathlib import Path
from src.datacenter.datawarehouse import DataWarehouse, DatasetConfig

TEST_DW = ".young/test_dw_unit"

@pytest.fixture
def dw():
    dw = DataWarehouse(TEST_DW)
    yield dw
    if Path(TEST_DW).exists():
        shutil.rmtree(TEST_DW)

def test_register_dataset(dw):
    """测试注册数据集"""
    config = DatasetConfig(name="test_ds", tags=["test"])
    result = dw.register_dataset(config)
    assert result == True

def test_list_datasets(dw):
    """测试列出数据集"""
    config = DatasetConfig(name="ds1", description="desc1")
    dw.register_dataset(config)
    datasets = dw.list_datasets()
    assert len(datasets) >= 1

def test_export_dataset_json(dw):
    """测试导出 JSON 格式"""
    dw.register_dataset(DatasetConfig(name="export_test"))
    path = dw.export_dataset("export_test", "json")
    assert path is not None
    assert Path(path).suffix == ".json"
```

### 2.6 企业功能测试

```python
# test_enterprise.py
import pytest
import shutil
from pathlib import Path
from src.datacenter.enterprise import EnterpriseManager, Permission

TEST_ENT = ".young/test_ent_unit"

@pytest.fixture
def em():
    em = EnterpriseManager(TEST_ENT)
    yield em
    if Path(TEST_ENT).exists():
        shutil.rmtree(TEST_ENT)

def test_create_tenant(em):
    """测试创建租户"""
    tenant = em.create_tenant("t1", "Test Company")
    assert tenant.tenant_id == "t1"
    assert tenant.name == "Test Company"

def test_create_user(em):
    """测试创建用户"""
    em.create_tenant("t2", "Company")
    user = em.create_user("u1", "t2", "admin", "admin@test.com", password="pass")
    assert user.username == "admin"

def test_authenticate(em):
    """测试用户认证"""
    em.create_tenant("t3", "Company")
    em.create_user("u2", "t3", "user", "user@test.com", password="password123")
    auth = em.authenticate("user", "password123", "t3")
    assert auth is not None

def test_check_permission_admin(em):
    """测试管理员权限"""
    em.create_tenant("t4", "Company")
    user = em.create_user("u3", "t4", "admin", role="admin", permissions=[Permission.ADMIN])
    assert em.check_permission(user, Permission.DELETE) == True

def test_audit_log(em):
    """测试审计日志"""
    em.log_audit("t5", "u5", "create", "agent", "a1")
    logs = em.query_audit_logs(tenant_id="t5")
    assert len(logs) >= 1

def test_audit_stats(em):
    """测试审计统计"""
    em.log_audit("t6", "u6", "read", "agent", "a1")
    em.log_audit("t6", "u6", "write", "agent", "a2")
    stats = em.get_audit_stats("t6")
    assert stats["total"] >= 2
```

---

## 3. 执行计划

### 3.1 测试执行顺序

```
1. 数据模型测试 (test_models.py)
   ↓
2. 工作空间测试 (test_workspace.py)
   ↓
3. 隔离控制测试 (test_isolation.py)
   ↓
4. Checkpoint 测试 (test_checkpoint.py)
   ↓
5. Trace 测试 (test_trace.py) - 已存在
   ↓
6. 数据仓库测试 (test_datawarehouse.py)
   ↓
7. 追踪导出测试 (test_tracing.py)
   ↓
8. 企业功能测试 (test_enterprise.py)
   ↓
9. 集成测试 (test_integration.py)
```

### 3.2 测试命令

```bash
# 运行所有测试
pytest tests/datacenter/ -v

# 运行单个测试文件
pytest tests/datacenter/test_workspace.py -v

# 运行单个测试
pytest tests/datacenter/test_workspace.py::test_create_workspace -v

# 生成覆盖率报告
pytest tests/datacenter/ --cov=src/datacenter --cov-report=html
```

---

## 4. 验收标准

| 测试类别 | 通过率要求 | 说明 |
|----------|------------|------|
| 单元测试 | 100% | 所有数据模型方法 |
| 集成测试 | 95% | 跨模块功能 |
| 功能测试 | 100% | 核心功能 |
| 隔离测试 | 100% | 数据隔离验证 |

### 4.1 核心功能验收

- [ ] AgentRunData 创建和序列化正常
- [ ] Workspace 创建/复制/归档功能正常
- [ ] Session/User/Agent 隔离正常
- [ ] Checkpoint 保存和加载正常
- [ ] Trace 收集和查询正常
- [ ] 数据集导出功能正常
- [ ] OpenTelemetry 格式正确
- [ ] LangSmith 格式正确
- [ ] 多租户隔离正常
- [ ] 权限检查正常
- [ ] 审计日志记录正常

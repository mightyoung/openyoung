"""
DataCenter Advanced Tests - Unified Store, Execution Record, Analytics
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch

from src.datacenter.execution_record import ExecutionRecord, ExecutionStatus
from src.datacenter.unified_store import UnifiedStore
from src.datacenter.analytics import DataAnalytics


class TestExecutionRecord:
    """Test ExecutionRecord"""

    def test_record_creation(self):
        record = ExecutionRecord(
            agent_name="test-agent",
            task_description="Test task"
        )
        assert record.agent_name == "test-agent"
        assert record.task_description == "Test task"
        assert record.execution_id is not None

    def test_status_constants(self):
        assert ExecutionStatus.PENDING == "pending"
        assert ExecutionStatus.RUNNING == "running"
        assert ExecutionStatus.SUCCESS == "success"
        assert ExecutionStatus.FAILED == "failed"

    def test_record_hierarchy(self):
        record = ExecutionRecord(
            execution_id="exec-1",
            run_id="run-1",
            step_id="step-1"
        )
        assert record.execution_id == "exec-1"
        assert record.run_id == "run-1"
        assert record.step_id == "step-1"

    def test_token_tracking(self):
        record = ExecutionRecord(
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150,
            cost_usd=0.001
        )
        assert record.prompt_tokens == 100
        assert record.completion_tokens == 50
        assert record.total_tokens == 150

    def test_duration_calculation(self):
        start = datetime(2026, 1, 1, 12, 0, 0)
        end = datetime(2026, 1, 1, 12, 0, 10)
        record = ExecutionRecord(
            start_time=start,
            end_time=end,
            duration_ms=10000
        )
        assert record.duration_ms == 10000


class TestUnifiedStore:
    """Test UnifiedStore"""

    def test_store_initialization(self, tmp_path):
        store = UnifiedStore(db_path=str(tmp_path / "test.db"))
        assert store is not None
        assert store.db_path is not None

    @pytest.mark.asyncio
    async def test_save_and_get(self, tmp_path):
        store = UnifiedStore(db_path=str(tmp_path / "test.db"))

        record = ExecutionRecord(
            agent_name="test",
            task_description="test task",
            status=ExecutionStatus.SUCCESS
        )

        store.save(record)
        retrieved = store.get(record.execution_id)

        assert retrieved is not None
        assert retrieved.agent_name == "test"

    @pytest.mark.asyncio
    async def test_list_records(self, tmp_path):
        store = UnifiedStore(db_path=str(tmp_path / "test.db"))

        # Create multiple records
        for i in range(3):
            record = ExecutionRecord(
                agent_name=f"agent-{i}",
                task_description=f"task-{i}"
            )
            store.save(record)

        records = store.list_recent(limit=10)
        assert len(records) >= 3

    @pytest.mark.asyncio
    async def test_update_status(self, tmp_path):
        store = UnifiedStore(db_path=str(tmp_path / "test.db"))

        record = ExecutionRecord(
            agent_name="test",
            status=ExecutionStatus.PENDING
        )
        store.save(record)

        store.update_status(record.execution_id, ExecutionStatus.SUCCESS)
        updated = store.get(record.execution_id)

        assert updated.status == ExecutionStatus.SUCCESS


class TestDataAnalytics:
    """Test DataAnalytics"""

    def test_analytics_creation(self):
        analytics = DataAnalytics()
        assert analytics is not None

    def test_get_agent_stats(self):
        """Test get_agent_stats method"""
        analytics = DataAnalytics()
        # This may return empty if no data
        stats = analytics.get_agent_stats("test-agent", days=1)
        assert isinstance(stats, dict)

    def test_get_task_stats(self):
        """Test get_task_stats method"""
        analytics = DataAnalytics()
        stats = analytics.get_task_stats(days=1)
        assert isinstance(stats, dict)

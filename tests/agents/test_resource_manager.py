"""
Tests for ResourceManager - Resource Allocation Management

Tests the ResourceManager class that manages memory, concurrency, and timeouts.
"""

import pytest
from unittest.mock import MagicMock


class TestResourceManager:
    """Test ResourceManager class"""

    def test_initialization_defaults(self):
        """Test ResourceManager initialization with defaults"""
        from src.agents.harness.resource_manager import ResourceManager

        rm = ResourceManager()

        assert rm._max_memory_mb == 512
        assert rm._max_concurrent_tasks == 4
        assert rm._default_timeout_seconds == 300
        assert rm._active_tasks == {}

    def test_initialization_custom(self):
        """Test ResourceManager initialization with custom values"""
        from src.agents.harness.resource_manager import ResourceManager

        rm = ResourceManager(
            max_memory_mb=1024,
            max_concurrent_tasks=8,
            default_timeout_seconds=600,
        )

        assert rm._max_memory_mb == 1024
        assert rm._max_concurrent_tasks == 8
        assert rm._default_timeout_seconds == 600

    def test_allocate_single_task(self):
        """Test allocating resources for a single task"""
        from src.agents.harness.resource_manager import ResourceManager

        rm = ResourceManager()
        result = rm.allocate("task-1")

        assert result["allocated"] is True
        assert result["task_id"] == "task-1"
        assert result["memory_mb"] == 512  # default
        assert result["timeout_seconds"] == 300  # default
        assert "task-1" in rm._active_tasks

    def test_allocate_with_custom_resources(self):
        """Test allocating with custom memory and timeout"""
        from src.agents.harness.resource_manager import ResourceManager

        rm = ResourceManager()
        result = rm.allocate("task-1", memory_mb=256, timeout_seconds=120)

        assert result["allocated"] is True
        assert result["memory_mb"] == 256
        assert result["timeout_seconds"] == 120

    def test_allocate_max_concurrent_reached(self):
        """Test allocation fails when max concurrent tasks reached"""
        from src.agents.harness.resource_manager import ResourceManager

        rm = ResourceManager(max_concurrent_tasks=2)

        # Allocate first two tasks
        result1 = rm.allocate("task-1")
        result2 = rm.allocate("task-2")

        assert result1["allocated"] is True
        assert result2["allocated"] is True

        # Third allocation should fail
        result3 = rm.allocate("task-3")

        assert result3["allocated"] is False
        assert result3["reason"] == "max_concurrent_tasks_reached"

    def test_allocate_multiple_tasks(self):
        """Test allocating multiple tasks"""
        from src.agents.harness.resource_manager import ResourceManager

        rm = ResourceManager(max_concurrent_tasks=4)

        rm.allocate("task-1")
        rm.allocate("task-2")
        rm.allocate("task-3")

        assert len(rm._active_tasks) == 3

    def test_release_task(self):
        """Test releasing resources for a task"""
        from src.agents.harness.resource_manager import ResourceManager

        rm = ResourceManager()
        rm.allocate("task-1")
        rm.allocate("task-2")

        assert len(rm._active_tasks) == 2

        rm.release("task-1")

        assert len(rm._active_tasks) == 1
        assert "task-1" not in rm._active_tasks
        assert "task-2" in rm._active_tasks

    def test_release_nonexistent_task(self):
        """Test releasing a task that doesn't exist"""
        from src.agents.harness.resource_manager import ResourceManager

        rm = ResourceManager()
        rm.allocate("task-1")

        # Should not raise
        rm.release("nonexistent")

        assert len(rm._active_tasks) == 1

    def test_release_allows_new_allocation(self):
        """Test that releasing a task allows new allocation"""
        from src.agents.harness.resource_manager import ResourceManager

        rm = ResourceManager(max_concurrent_tasks=2)

        rm.allocate("task-1")
        rm.allocate("task-2")

        # Should fail - at max
        result = rm.allocate("task-3")
        assert result["allocated"] is False

        # Release first task
        rm.release("task-1")

        # Should succeed now
        result = rm.allocate("task-3")
        assert result["allocated"] is True

    def test_get_stats_empty(self):
        """Test get_stats with no active tasks"""
        from src.agents.harness.resource_manager import ResourceManager

        rm = ResourceManager()
        stats = rm.get_stats()

        assert stats["active_tasks"] == 0
        assert stats["max_concurrent_tasks"] == 4
        assert stats["max_memory_mb"] == 512
        assert stats["default_timeout_seconds"] == 300

    def test_get_stats_with_tasks(self):
        """Test get_stats with active tasks"""
        from src.agents.harness.resource_manager import ResourceManager

        rm = ResourceManager(max_memory_mb=1024, max_concurrent_tasks=8)
        rm.allocate("task-1")
        rm.allocate("task-2")

        stats = rm.get_stats()

        assert stats["active_tasks"] == 2
        assert stats["max_concurrent_tasks"] == 8
        assert stats["max_memory_mb"] == 1024


class TestResourceManagerEdgeCases:
    """Edge case tests for ResourceManager"""

    def test_allocate_same_task_twice(self):
        """Test allocating the same task ID twice"""
        from src.agents.harness.resource_manager import ResourceManager

        rm = ResourceManager()
        result1 = rm.allocate("task-1")
        result2 = rm.allocate("task-1")

        # Both succeed - second call just overwrites
        assert result1["allocated"] is True
        assert result2["allocated"] is True
        assert len(rm._active_tasks) == 1

    def test_release_and_reallocate(self):
        """Test releasing and reallocating same task"""
        from src.agents.harness.resource_manager import ResourceManager

        rm = ResourceManager()

        rm.allocate("task-1")
        rm.release("task-1")
        result = rm.allocate("task-1")

        assert result["allocated"] is True
        assert result["task_id"] == "task-1"

    def test_zero_max_concurrent(self):
        """Test with zero max concurrent tasks"""
        from src.agents.harness.resource_manager import ResourceManager

        rm = ResourceManager(max_concurrent_tasks=0)

        result = rm.allocate("task-1")

        assert result["allocated"] is False
        assert result["reason"] == "max_concurrent_tasks_reached"

    def test_allocation_tracks_individual_resources(self):
        """Test that allocations track individual resource values"""
        from src.agents.harness.resource_manager import ResourceManager

        rm = ResourceManager()

        rm.allocate("task-1", memory_mb=100)
        rm.allocate("task-2", memory_mb=200)

        assert rm._active_tasks["task-1"]["memory_mb"] == 100
        assert rm._active_tasks["task-2"]["memory_mb"] == 200

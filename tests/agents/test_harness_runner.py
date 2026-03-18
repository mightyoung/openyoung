"""
Tests for HarnessRunner - Harness Lifecycle Management

Tests the HarnessRunner class that manages Harness start, record_step,
get_status, and save operations.
"""

import pytest
from unittest.mock import MagicMock, patch


class MockHarness:
    """Mock Harness instance for testing"""

    def __init__(self):
        self._started = False
        self._steps = []
        self._status = {"status": "idle", "total_steps": 0}

    def start(self):
        self._started = True
        self._status["status"] = "running"

    def record_step(self, success: bool):
        self._steps.append({"success": success})
        self._status["total_steps"] = len(self._steps)
        if success:
            self._status["successful_steps"] = self._status.get("successful_steps", 0) + 1

    def get_status(self):
        return self._status.copy()

    def save(self, path: str):
        self._saved_path = path


class TestHarnessRunner:
    """Test HarnessRunner class"""

    def test_initialization_with_none(self):
        """Test HarnessRunner initialization with None harness"""
        from src.agents.harness.harness_runner import HarnessRunner

        runner = HarnessRunner(harness=None)
        assert runner._harness is None
        assert runner.harness is None

    def test_initialization_with_harness(self):
        """Test HarnessRunner initialization with mock harness"""
        from src.agents.harness.harness_runner import HarnessRunner

        mock_harness = MockHarness()
        runner = HarnessRunner(harness=mock_harness)
        assert runner.harness is mock_harness

    def test_start_with_no_harness(self):
        """Test start() does nothing when harness is None"""
        from src.agents.harness.harness_runner import HarnessRunner

        runner = HarnessRunner(harness=None)
        runner.start()  # Should not raise

    def test_start_with_harness(self):
        """Test start() calls harness.start()"""
        from src.agents.harness.harness_runner import HarnessRunner

        mock_harness = MockHarness()
        runner = HarnessRunner(harness=mock_harness)

        runner.start()

        assert mock_harness._started is True
        assert mock_harness._status["status"] == "running"

    def test_record_step_with_no_harness(self):
        """Test record_step() does nothing when harness is None"""
        from src.agents.harness.harness_runner import HarnessRunner

        runner = HarnessRunner(harness=None)
        runner.record_step(True)  # Should not raise

    def test_record_step_success(self):
        """Test record_step() with success=True"""
        from src.agents.harness.harness_runner import HarnessRunner

        mock_harness = MockHarness()
        runner = HarnessRunner(harness=mock_harness)

        runner.record_step(True)

        assert len(mock_harness._steps) == 1
        assert mock_harness._steps[0]["success"] is True

    def test_record_step_failure(self):
        """Test record_step() with success=False"""
        from src.agents.harness.harness_runner import HarnessRunner

        mock_harness = MockHarness()
        runner = HarnessRunner(harness=mock_harness)

        runner.record_step(False)

        assert len(mock_harness._steps) == 1
        assert mock_harness._steps[0]["success"] is False

    def test_get_status_with_no_harness(self):
        """Test get_status() returns empty dict when harness is None"""
        from src.agents.harness.harness_runner import HarnessRunner

        runner = HarnessRunner(harness=None)
        status = runner.get_status()

        assert status == {}

    def test_get_status_with_harness(self):
        """Test get_status() returns harness status"""
        from src.agents.harness.harness_runner import HarnessRunner

        mock_harness = MockHarness()
        runner = HarnessRunner(harness=mock_harness)

        mock_harness.start()
        mock_harness.record_step(True)

        status = runner.get_status()

        assert status["status"] == "running"
        assert status["total_steps"] == 1

    def test_save_with_no_harness(self):
        """Test save() does nothing when harness is None"""
        from src.agents.harness.harness_runner import HarnessRunner

        runner = HarnessRunner(harness=None)
        runner.save("/tmp/test.json")  # Should not raise

    def test_save_with_harness(self):
        """Test save() calls harness.save() with path"""
        from src.agents.harness.harness_runner import HarnessRunner

        mock_harness = MockHarness()
        runner = HarnessRunner(harness=mock_harness)

        runner.save("/tmp/test.json")

        assert mock_harness._saved_path == "/tmp/test.json"

    def test_set_harness(self):
        """Test set_harness() updates the harness instance"""
        from src.agents.harness.harness_runner import HarnessRunner

        runner = HarnessRunner(harness=None)
        assert runner.harness is None

        mock_harness = MockHarness()
        runner.set_harness(mock_harness)

        assert runner.harness is mock_harness

    def test_multiple_record_steps(self):
        """Test multiple record_step() calls"""
        from src.agents.harness.harness_runner import HarnessRunner

        mock_harness = MockHarness()
        runner = HarnessRunner(harness=mock_harness)

        runner.record_step(True)
        runner.record_step(True)
        runner.record_step(False)

        assert len(mock_harness._steps) == 3
        assert mock_harness._status["total_steps"] == 3


class TestHarnessRunnerIntegration:
    """Integration tests for HarnessRunner with real Harness"""

    def test_harness_runner_with_mock_harness_lifecycle(self):
        """Test complete HarnessRunner lifecycle with mock harness"""
        from src.agents.harness.harness_runner import HarnessRunner

        mock_harness = MockHarness()
        runner = HarnessRunner(harness=mock_harness)

        # Start
        runner.start()
        status = runner.get_status()
        assert status["status"] == "running"

        # Record steps
        runner.record_step(True)
        runner.record_step(True)
        runner.record_step(False)

        status = runner.get_status()
        assert status["total_steps"] == 3

        # Save
        runner.save("/tmp/harness_state.json")
        assert mock_harness._saved_path == "/tmp/harness_state.json"

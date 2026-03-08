"""
Harness Module Tests
"""

from src.harness import Harness, HarnessStats, HarnessStatus


class TestHarness:
    """Test Harness functionality"""

    def test_harness_initialization(self):
        """Test Harness initialization"""
        harness = Harness()
        assert harness.status == HarnessStatus.IDLE
        assert harness.start_time is None
        assert harness.stats.total_steps == 0

    def test_harness_start(self):
        """Test Harness start"""
        harness = Harness()
        harness.start()

        assert harness.status == HarnessStatus.RUNNING
        assert harness.start_time is not None
        assert harness.stats.start_time is not None

    def test_harness_pause(self):
        """Test Harness pause"""
        harness = Harness()
        harness.start()
        harness.pause()

        assert harness.status == HarnessStatus.PAUSED

    def test_harness_resume(self):
        """Test Harness resume"""
        harness = Harness()
        harness.start()
        harness.pause()
        harness.resume()

        assert harness.status == HarnessStatus.RUNNING

    def test_harness_stop(self):
        """Test Harness stop"""
        harness = Harness()
        harness.start()
        harness.record_step(True)
        harness.record_step(True)
        harness.record_step(False)

        stats = harness.stop()

        assert harness.status == HarnessStatus.STOPPED
        assert stats.total_steps == 3
        assert stats.successful_steps == 2
        assert stats.failed_steps == 1
        assert stats.end_time is not None

    def test_harness_record_step_success(self):
        """Test recording successful step"""
        harness = Harness()
        harness.start()
        harness.record_step(True)

        assert harness.stats.total_steps == 1
        assert harness.stats.successful_steps == 1
        assert harness.stats.failed_steps == 0

    def test_harness_record_step_failure(self):
        """Test recording failed step"""
        harness = Harness()
        harness.start()
        harness.record_step(False)

        assert harness.stats.total_steps == 1
        assert harness.stats.successful_steps == 0
        assert harness.stats.failed_steps == 1

    def test_harness_get_status(self):
        """Test getting harness status"""
        harness = Harness()
        harness.start()
        harness.record_step(True)
        harness.set_metadata("key", "value")

        status = harness.get_status()

        assert status["status"] == "running"
        assert status["total_steps"] == 1
        assert status["successful_steps"] == 1
        assert status["metadata"]["key"] == "value"

    def test_harness_metadata(self):
        """Test harness metadata operations"""
        harness = Harness()

        harness.set_metadata("name", "test")
        harness.set_metadata("count", 42)

        assert harness.get_metadata("name") == "test"
        assert harness.get_metadata("count") == 42
        assert harness.get_metadata("nonexistent") is None

    def test_harness_cannot_pause_from_idle(self):
        """Test that pause from IDLE does nothing"""
        harness = Harness()
        harness.pause()

        assert harness.status == HarnessStatus.IDLE

    def test_harness_cannot_resume_from_idle(self):
        """Test that resume from IDLE does nothing"""
        harness = Harness()
        harness.resume()

        assert harness.status == HarnessStatus.IDLE


class TestHarnessStats:
    """Test HarnessStats dataclass"""

    def test_harness_stats_defaults(self):
        """Test HarnessStats default values"""
        stats = HarnessStats()

        assert stats.total_steps == 0
        assert stats.successful_steps == 0
        assert stats.failed_steps == 0
        assert stats.start_time is None
        assert stats.end_time is None

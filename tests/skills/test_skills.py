"""
Skills Module Tests
"""

import pytest

from src.skills import (
    HeartbeatConfig,
    HeartbeatPhase,
    HeartbeatResult,
    HeartbeatScheduler,
    LearningsManager,
    LearningType,
    Priority,
    ReleaseType,
    Skill,
    SkillManager,
    SkillVersion,
)


class TestSkillManager:
    """Test SkillManager functionality"""

    def test_manager_initialization(self):
        """Test SkillManager initialization"""
        manager = SkillManager()
        assert manager._skills == {}
        assert manager._skill_paths == []

    def test_register_skill(self):
        """Test registering a skill"""
        manager = SkillManager()

        def handler():
            return "executed"

        skill = Skill(name="test_skill", handler=handler, description="A test skill")
        manager.register(skill)

        assert "test_skill" in manager.list_skills()

    def test_unregister_skill(self):
        """Test unregistering a skill"""
        manager = SkillManager()

        skill = Skill(name="to_remove", handler=lambda: None)
        manager.register(skill)
        result = manager.unregister("to_remove")

        assert result is True
        assert "to_remove" not in manager.list_skills()

    def test_unregister_nonexistent_skill(self):
        """Test unregistering nonexistent skill"""
        manager = SkillManager()

        result = manager.unregister("nonexistent")

        assert result is False

    def test_load_skill(self):
        """Test loading a skill"""
        manager = SkillManager()

        skill = Skill(name="loadable", handler=lambda: "result", is_loaded=False)
        manager.register(skill)
        loaded = manager.load("loadable")

        assert loaded is not None
        assert loaded.is_loaded is True

    def test_load_nonexistent_skill(self):
        """Test loading nonexistent skill"""
        manager = SkillManager()

        loaded = manager.load("nonexistent")

        assert loaded is None

    def test_unload_skill(self):
        """Test unloading a skill"""
        manager = SkillManager()

        skill = Skill(name="unloadable", handler=lambda: None, is_loaded=True)
        manager.register(skill)
        result = manager.unload("unloadable")

        assert result is True
        assert skill.is_loaded is False

    def test_list_skills(self):
        """Test listing all skills"""
        manager = SkillManager()

        manager.register(Skill(name="skill1", handler=lambda: None))
        manager.register(Skill(name="skill2", handler=lambda: None))

        skills = manager.list_skills()

        assert len(skills) == 2
        assert "skill1" in skills
        assert "skill2" in skills

    def test_get_skill(self):
        """Test getting a skill"""
        manager = SkillManager()

        skill = Skill(name="getable", handler=lambda: None)
        manager.register(skill)
        retrieved = manager.get_skill("getable")

        assert retrieved is not None
        assert retrieved.name == "getable"

    def test_get_nonexistent_skill(self):
        """Test getting nonexistent skill"""
        manager = SkillManager()

        retrieved = manager.get_skill("nonexistent")

        assert retrieved is None

    def test_execute_skill(self):
        """Test executing a skill"""
        manager = SkillManager()

        def my_handler(x, y):
            return x + y

        skill = Skill(name="adder", handler=my_handler, is_loaded=True)
        manager.register(skill)

        result = manager.execute_skill("adder", 3, 5)

        assert result == 8

    def test_execute_unloaded_skill(self):
        """Test executing unloaded skill raises error"""
        manager = SkillManager()

        skill = Skill(name="unloaded", handler=lambda: None, is_loaded=False)
        manager.register(skill)

        with pytest.raises(ValueError, match="not loaded"):
            manager.execute_skill("unloaded")

    def test_execute_nonexistent_skill(self):
        """Test executing nonexistent skill raises error"""
        manager = SkillManager()

        with pytest.raises(ValueError, match="not loaded"):
            manager.execute_skill("nonexistent")

    def test_add_skill_path(self):
        """Test adding skill path"""
        manager = SkillManager()

        manager.add_skill_path("/path/to/skills")

        assert "/path/to/skills" in manager.get_skill_paths()

    def test_get_skill_paths(self):
        """Test getting skill paths"""
        manager = SkillManager()

        manager.add_skill_path("/path1")
        manager.add_skill_path("/path2")

        paths = manager.get_skill_paths()

        assert len(paths) == 2
        assert "/path1" in paths
        assert "/path2" in paths

    def test_discover_skills_nonexistent_path(self):
        """Test discovering skills from nonexistent path"""
        manager = SkillManager()

        discovered = manager.discover_skills("/nonexistent/path")

        assert discovered == []


class TestSkill:
    """Test Skill dataclass"""

    def test_skill_defaults(self):
        """Test Skill default values"""
        skill = Skill(name="test", handler=lambda: None)

        assert skill.name == "test"
        assert skill.description == ""
        assert skill.is_loaded is False

    def test_skill_with_values(self):
        """Test Skill with custom values"""

        def handler():
            return "result"

        skill = Skill(
            name="custom", handler=handler, description="Custom skill", is_loaded=True
        )

        assert skill.name == "custom"
        assert skill.handler() == "result"
        assert skill.description == "Custom skill"
        assert skill.is_loaded is True


# ============ 新增模块测试 ============


class TestHeartbeatConfig:
    """Test HeartbeatConfig"""

    def test_default_config(self):
        """Test default heartbeat config"""
        config = HeartbeatConfig()
        assert config.interval_seconds == 14400
        assert config.enabled is True
        assert len(config.phases_enabled) > 0

    def test_custom_config(self):
        """Test custom heartbeat config"""
        config = HeartbeatConfig(interval_seconds=60, enabled=False)
        assert config.interval_seconds == 60
        assert config.enabled is False


class TestHeartbeatScheduler:
    """Test HeartbeatScheduler"""

    @pytest.mark.asyncio
    async def test_scheduler_initialization(self):
        """Test scheduler initialization"""
        scheduler = HeartbeatScheduler()
        assert scheduler.is_running() is False
        assert scheduler.config.interval_seconds == 14400

    @pytest.mark.asyncio
    async def test_register_callback(self):
        """Test callback registration"""
        scheduler = HeartbeatScheduler()

        async def my_callback():
            return HeartbeatResult(
                phase=HeartbeatPhase.INFO_INTAKE,
                success=True,
                message="test",
            )

        scheduler.register_callback(HeartbeatPhase.INFO_INTAKE, my_callback)
        assert len(scheduler._callbacks[HeartbeatPhase.INFO_INTAKE]) == 1


class TestSkillVersion:
    """Test SkillVersion"""

    def test_version_parsing(self):
        """Test version parsing"""
        v = SkillVersion.parse("v1.2.3")
        assert v is not None
        assert v.major == 1
        assert v.minor == 2
        assert v.patch == 3

    def test_version_to_string(self):
        """Test version to string"""
        v = SkillVersion(2, 0, 1)
        assert str(v) == "v2.0.1"

    def test_version_comparison(self):
        """Test version comparison"""
        v1 = SkillVersion(1, 0, 0)
        v2 = SkillVersion(1, 1, 0)
        v3 = SkillVersion(2, 0, 0)

        assert v1 < v2
        assert v2 < v3
        assert v1 == SkillVersion(1, 0, 0)

    def test_version_bump(self):
        """Test version bump"""
        v = SkillVersion(1, 2, 3)

        assert v.bump(ReleaseType.PATCH) == SkillVersion(1, 2, 4)
        assert v.bump(ReleaseType.MINOR) == SkillVersion(1, 3, 0)
        assert v.bump(ReleaseType.MAJOR) == SkillVersion(2, 0, 0)


class TestLearningsManager:
    """Test LearningsManager"""

    @pytest.mark.asyncio
    async def test_log_learning(self, tmp_path):
        """Test logging a learning"""
        manager = LearningsManager(workspace=tmp_path)

        entry = await manager.log_learning(
            title="Test learning",
            description="This is a test",
            tags=["test", "example"],
        )

        assert entry.type == LearningType.LEARNING
        assert entry.title == "Test learning"
        assert "test" in entry.tags

    @pytest.mark.asyncio
    async def test_log_error(self, tmp_path):
        """Test logging an error"""
        manager = LearningsManager(workspace=tmp_path)

        try:
            raise ValueError("Test error")
        except ValueError as e:
            entry = await manager.log_error(
                error=e,
                context={"operation": "test"},
                solution="Fixed by doing X",
            )

        assert entry.type == LearningType.ERROR
        assert entry.solution == "Fixed by doing X"


class TestPriority:
    """Test Priority enum"""

    def test_priority_order(self):
        """Test priority ordering"""
        assert Priority.CRITICAL.value == "critical"
        assert Priority.HIGH.value == "high"
        assert Priority.MEDIUM.value == "medium"
        assert Priority.LOW.value == "low"

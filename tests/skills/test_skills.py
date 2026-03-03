"""
Skills Module Tests
"""

import pytest
from src.skills import SkillManager, Skill


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

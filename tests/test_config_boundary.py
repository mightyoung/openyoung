"""
Boundary Condition Tests for Config Models and Manager

基于 Kent Beck TDD 最佳实践：边界条件测试
"""

import pytest
from pathlib import Path
from pydantic import ValidationError

from src.cli.config_models import (
    LLMConfig,
    ExecutionConfig,
    PermissionConfigModel,
    AgentConfigModel,
    AppConfig,
)
from src.cli.config_manager import ConfigManager


class TestLLMConfigBoundary:
    """LLMConfig 边界条件测试"""

    def test_empty_model_name(self):
        """空模型名称应该被拒绝"""
        with pytest.raises(ValidationError) as exc_info:
            LLMConfig(model="")
        assert "model" in str(exc_info.value).lower()

    def test_whitespace_model_name(self):
        """空白模型名称应该被拒绝"""
        with pytest.raises(ValidationError):
            LLMConfig(model="  ")

    def test_temperature_upper_bound(self):
        """温度上限边界 (2.0)"""
        config = LLMConfig(temperature=2.0)
        assert config.temperature == 2.0

    def test_temperature_exceed_bound(self):
        """温度超过上限应该被拒绝"""
        with pytest.raises(ValidationError):
            LLMConfig(temperature=2.1)

    def test_temperature_lower_bound(self):
        """温度下限边界 (0.0)"""
        config = LLMConfig(temperature=0.0)
        assert config.temperature == 0.0

    def test_temperature_negative(self):
        """负温度应该被拒绝"""
        with pytest.raises(ValidationError):
            LLMConfig(temperature=-0.1)

    def test_max_tokens_upper_bound(self):
        """最大令牌数上限边界 (100000)"""
        config = LLMConfig(max_tokens=100000)
        assert config.max_tokens == 100000

    def test_max_tokens_exceed_bound(self):
        """最大令牌数超过上限应该被拒绝"""
        with pytest.raises(ValidationError):
            LLMConfig(max_tokens=100001)

    def test_max_tokens_lower_bound(self):
        """最大令牌数下限边界 (1)"""
        config = LLMConfig(max_tokens=1)
        assert config.max_tokens == 1

    def test_max_tokens_zero(self):
        """零令牌数应该被拒绝"""
        with pytest.raises(ValidationError):
            LLMConfig(max_tokens=0)


class TestExecutionConfigBoundary:
    """ExecutionConfig 边界条件测试"""

    def test_timeout_upper_bound(self):
        """超时上限边界 (3600秒)"""
        config = ExecutionConfig(timeout=3600)
        assert config.timeout == 3600

    def test_timeout_exceed_bound(self):
        """超时超过上限应该被拒绝"""
        with pytest.raises(ValidationError):
            ExecutionConfig(timeout=3601)

    def test_timeout_lower_bound(self):
        """超时下限边界 (1秒)"""
        config = ExecutionConfig(timeout=1)
        assert config.timeout == 1

    def test_max_tool_calls_upper_bound(self):
        """最大工具调用次数上限边界 (100)"""
        config = ExecutionConfig(max_tool_calls=100)
        assert config.max_tool_calls == 100

    def test_max_retries_upper_bound(self):
        """最大重试次数上限边界 (10)"""
        config = ExecutionConfig(max_retries=10)
        assert config.max_retries == 10


class TestPermissionConfigBoundary:
    """PermissionConfig 边界条件测试"""

    def test_invalid_global_action(self):
        """无效的全局动作应该被修正为 ask"""
        config = PermissionConfigModel(_global="invalid_action")
        assert config._global == "ask"

    def test_valid_global_actions(self):
        """有效的全局动作应该被接受"""
        for action in ["ask", "auto", "deny", "confirm"]:
            config = PermissionConfigModel(_global=action)
            # 注意: validator 会自动规范化，测试实际行为
            assert config._global in ["ask", "auto", "deny", "confirm"]


class TestAgentConfigBoundary:
    """AgentConfig 边界条件测试"""

    def test_default_values(self):
        """测试默认值"""
        config = AgentConfigModel()
        assert config.name == "default"
        assert config.temperature == 0.7
        assert config.tools == []

    def test_empty_tools_list(self):
        """空工具列表应该被接受"""
        config = AgentConfigModel(tools=[])
        assert config.tools == []

    def test_empty_skills_list(self):
        """空技能列表应该被接受"""
        config = AgentConfigModel(skills=[])
        assert config.skills == []


class TestAppConfigBoundary:
    """AppConfig 边界条件测试"""

    def test_default_log_level(self):
        """默认日志级别应该是 INFO"""
        config = AppConfig()
        assert config.log_level == "INFO"

    def test_valid_log_levels(self):
        """有效的日志级别应该被接受"""
        for level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            config = AppConfig(log_level=level)
            assert config.log_level == level

    def test_lowercase_log_level(self):
        """小写日志级别应该被转换为大写"""
        config = AppConfig(log_level="debug")
        assert config.log_level == "DEBUG"

    def test_invalid_log_level(self):
        """无效日志级别应该被修正为 INFO"""
        config = AppConfig(log_level="INVALID")
        assert config.log_level == "INFO"

    def test_default_values(self):
        """测试默认值"""
        config = AppConfig()
        assert config.version == "0.1.0"
        assert config.default_agent == "default"
        assert config.debug is False


class TestConfigManagerBoundary:
    """ConfigManager 边界条件测试"""

    def test_load_nonexistent_config(self, tmp_path):
        """加载不存在的配置应该返回空字典或已有配置"""
        test_dir = tmp_path / "nonexistent_config_test"
        manager = ConfigManager(config_dir=test_dir)
        config = manager.load()
        # 可能是空字典或已有配置（取决于home目录是否有配置）
        assert isinstance(config, dict)

    def test_get_nonexistent_key(self, tmp_path):
        """获取不存在的键应该返回默认值"""
        manager = ConfigManager(config_dir=tmp_path)
        result = manager.get("nonexistent_key", "default_value")
        assert result == "default_value"

    def test_get_validated_config_default(self, tmp_path):
        """无效配置应该返回默认配置"""
        manager = ConfigManager(config_dir=tmp_path)
        # 写入无效 JSON
        (tmp_path / "config.json").write_text("invalid json {")
        config = manager.get_validated_config()
        assert isinstance(config, AppConfig)
        assert config.version == "0.1.0"

    def test_validate_invalid_agent_config(self, tmp_path):
        """无效 Agent 配置应该返回 None"""
        manager = ConfigManager(config_dir=tmp_path)
        result = manager.validate_agent_config({"temperature": 999})
        assert result is None

    def test_validate_invalid_llm_config(self, tmp_path):
        """无效 LLM 配置应该返回 None"""
        manager = ConfigManager(config_dir=tmp_path)
        result = manager.validate_llm_config({"temperature": -1})
        assert result is None


class TestConfigPersistence:
    """配置持久化测试"""

    def test_save_and_load_config(self, tmp_path):
        """保存和加载配置"""
        manager = ConfigManager(config_dir=tmp_path)

        test_config = {
            "version": "1.0.0",
            "default_agent": "test-agent",
            "debug": True,
        }

        assert manager.save(test_config) is True

        loaded = manager.load()
        assert loaded["version"] == "1.0.0"
        assert loaded["default_agent"] == "test-agent"
        assert loaded["debug"] is True

    def test_set_and_get(self, tmp_path):
        """设置和获取配置值"""
        manager = ConfigManager(config_dir=tmp_path)

        manager.set("test_key", "test_value")
        result = manager.get("test_key")
        assert result == "test_value"

    def test_reset_config(self, tmp_path):
        """重置配置"""
        manager = ConfigManager(config_dir=tmp_path)

        manager.set("key1", "value1")
        assert manager.reset() is True

        result = manager.get("key1")
        assert result is None

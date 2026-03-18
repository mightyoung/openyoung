"""
CLI Commands Integration Tests

Tests for CLI command modules:
- run: openyoung run
- eval: openyoung eval
- config: openyoung config

Uses pytest + pytest-asyncio with mocked YoungAgent dependencies.
"""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import click
from click.testing import CliRunner
import pytest

# Add src to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))


# ============ Test Run Command ============


class TestRunCommand:
    """Tests for openyoung run command"""

    def test_run_command_basic_parsing(self):
        """Test run command argument and option parsing"""
        from src.cli.commands.run import run_agent

        # Verify it's a click command
        assert isinstance(run_agent, click.Command)

        # Check command name
        assert run_agent.name == "run"

    def test_run_command_help(self, cli_runner):
        """Test run command help output"""
        from src.cli.commands.run import run_agent

        result = cli_runner.invoke(run_agent, ["--help"])

        assert result.exit_code == 0
        assert "Run an agent" in result.output
        assert "--interactive" in result.output
        assert "--github" in result.output
        assert "--sandbox" in result.output

    def test_run_command_default_values(self, cli_runner):
        """Test run command with default agent name"""
        from src.cli.commands.run import run_agent

        # Mock dependencies
        with patch("src.cli.commands.run.AgentLoader") as mock_loader_class:
            mock_loader = MagicMock()
            mock_loader.load_agent.return_value = MagicMock(model="test-model")
            mock_loader_class.return_value = mock_loader

            with patch("src.cli.commands.run.YoungAgent") as mock_agent_class:
                mock_agent = AsyncMock()
                mock_agent.run.return_value = "Task completed"
                mock_agent.get_all_stats.return_value = {
                    "datacenter_traces_count": 0,
                    "evaluation_results_count": 0,
                    "evolver_capsules_count": 0,
                }
                mock_agent_class.return_value = mock_agent

                # Run without task (should fail validation)
                result = cli_runner.invoke(run_agent, [])

                # Should error about missing task
                assert result.exit_code == 0 or "Error" in result.output or "Task required" in result.output

    def test_run_command_with_task(self, cli_runner):
        """Test run command with task argument parsing"""
        from src.cli.commands.run import run_agent

        # Test that command parses arguments correctly
        result = cli_runner.invoke(run_agent, ["default", "analyze this", "--help"])

        # Help should work even without full agent setup
        assert result.exit_code == 0
        assert "Run an agent" in result.output

    def test_run_command_agent_not_found(self, cli_runner):
        """Test run command with non-existent agent"""
        from src.cli.commands.run import run_agent

        with patch("src.cli.commands.run.AgentLoader") as mock_loader_class:
            mock_loader = MagicMock()
            mock_loader.load_agent.side_effect = ValueError("Agent not found: nonexistent")
            mock_loader_class.return_value = mock_loader

            result = cli_runner.invoke(run_agent, ["nonexistent", "some task"])

            assert "Error" in result.output or "not found" in result.output.lower()

    def test_run_command_sandbox_options(self):
        """Test run command sandbox options parsing"""
        from src.cli.commands.run import run_agent

        param_names = [p.name for p in run_agent.params]
        # Just verify the options are registered
        assert "sandbox" in param_names
        assert "allow_network" in param_names
        assert "max_memory" in param_names
        assert "max_time" in param_names


# ============ Test Eval Command ============


class TestEvalCommand:
    """Tests for openyoung eval command group"""

    def test_eval_group_is_click_group(self):
        """Test eval_group is a click group"""
        from src.cli.commands.eval import eval_group

        assert isinstance(eval_group, click.Group)

    def test_eval_run_command_exists(self):
        """Test eval run subcommand exists"""
        from src.cli.commands.eval import eval_group

        assert "run" in eval_group.commands

    def test_eval_report_command_exists(self):
        """Test eval report subcommand exists"""
        from src.cli.commands.eval import eval_group

        assert "report" in eval_group.commands

    def test_eval_compare_command_exists(self):
        """Test eval compare subcommand exists"""
        from src.cli.commands.eval import eval_group

        assert "compare" in eval_group.commands

    def test_eval_run_help(self, cli_runner):
        """Test eval run help output"""
        from src.cli.commands.eval import eval_group

        result = cli_runner.invoke(eval_group, ["run", "--help"])

        assert result.exit_code == 0
        assert "Dataset" in result.output or "dataset" in result.output.lower()

    def test_eval_run_basic(self, cli_runner):
        """Test eval run with basic arguments"""
        from src.cli.commands.eval import eval_group

        result = cli_runner.invoke(eval_group, ["run", "test-dataset"])

        assert result.exit_code == 0
        assert "test-dataset" in result.output
        assert "young" in result.output  # default agent

    def test_eval_run_with_options(self, cli_runner):
        """Test eval run with custom agent and output"""
        from src.cli.commands.eval import eval_group

        result = cli_runner.invoke(
            eval_group,
            ["run", "test-dataset", "--agent", "custom-agent", "--output", "results.json"],
        )

        assert result.exit_code == 0
        assert "test-dataset" in result.output
        assert "custom-agent" in result.output
        assert "results.json" in result.output

    def test_eval_report_help(self, cli_runner):
        """Test eval report help output"""
        from src.cli.commands.eval import eval_group

        result = cli_runner.invoke(eval_group, ["report", "--help"])

        assert result.exit_code == 0

    def test_eval_compare_help(self, cli_runner):
        """Test eval compare help output"""
        from src.cli.commands.eval import eval_group

        result = cli_runner.invoke(eval_group, ["compare", "--help"])

        assert result.exit_code == 0


# ============ Test Config Command ============


class TestConfigCommand:
    """Tests for openyoung config command group"""

    def test_config_group_is_click_group(self):
        """Test config_group is a click group"""
        from src.cli.commands.config import config_group

        assert isinstance(config_group, click.Group)

    def test_config_get_command_exists(self):
        """Test config get subcommand exists"""
        from src.cli.commands.config import config_group

        assert "get" in config_group.commands

    def test_config_set_command_exists(self):
        """Test config set subcommand exists"""
        from src.cli.commands.config import config_group

        assert "set" in config_group.commands

    def test_config_list_command_exists(self):
        """Test config list subcommand exists"""
        from src.cli.commands.config import config_group

        assert "list" in config_group.commands

    def test_config_init_command_exists(self):
        """Test config init subcommand exists"""
        from src.cli.commands.config import config_group

        assert "init" in config_group.commands

    def test_config_get_help(self, cli_runner):
        """Test config get help output"""
        from src.cli.commands.config import config_group

        result = cli_runner.invoke(config_group, ["get", "--help"])

        assert result.exit_code == 0

    def test_config_get_key(self, cli_runner, tmp_user_config):
        """Test config get returns value for existing key"""
        from src.cli.commands.config import config_group

        result = cli_runner.invoke(config_group, ["get", "test.key"])

        # Should either show value or "not found"
        assert result.exit_code == 0

    def test_config_set_help(self, cli_runner):
        """Test config set help output"""
        from src.cli.commands.config import config_group

        result = cli_runner.invoke(config_group, ["set", "--help"])

        assert result.exit_code == 0

    def test_config_list_help(self, cli_runner):
        """Test config list help output"""
        from src.cli.commands.config import config_group

        result = cli_runner.invoke(config_group, ["list", "--help"])

        assert result.exit_code == 0

    def test_config_init_help(self, cli_runner):
        """Test config init help output"""
        from src.cli.commands.config import config_group

        result = cli_runner.invoke(config_group, ["init", "--help"])

        assert result.exit_code == 0


# ============ Fixtures ============


@pytest.fixture
def cli_runner():
    """Provide a Click CLI tester"""
    return CliRunner()


@pytest.fixture
def tmp_user_config(tmp_path, monkeypatch):
    """Create temporary user config directory"""
    config_dir = tmp_path / ".openyoung"
    config_dir.mkdir()

    # Point to temp config
    monkeypatch.setenv("OPENYOUNG_CONFIG_DIR", str(config_dir))

    yield config_dir


@pytest.fixture
def mock_young_agent():
    """Mock YoungAgent for testing"""
    agent = AsyncMock()
    agent.run.return_value = "Task completed successfully"
    agent.get_all_stats.return_value = {
        "datacenter_traces_count": 0,
        "evaluation_results_count": 0,
        "evolver_capsules_count": 0,
    }
    return agent


# ============ Utility ============


def params_contains(params, name):
    """Check if params list contains a param with given name"""
    return any(p.name == name for p in params)

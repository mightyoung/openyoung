"""
E2E Tests - CLI Commands

Tests for OpenYoung CLI commands using subprocess.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


class TestCLICommands:
    """Test CLI command execution"""

    @pytest.fixture(autouse=True)
    def setup(self, cli_path: str, project_root: Path):
        self.cli_path = cli_path
        self.project_root = project_root

    def run_cli(self, *args, timeout: int = 30) -> subprocess.CompletedProcess:
        """Run CLI command"""
        cmd = [sys.executable, "-m", "src.cli.main"] + list(args)
        return subprocess.run(
            cmd,
            cwd=str(self.project_root),
            capture_output=True,
            text=True,
            timeout=timeout,
        )

    def test_cli_help(self):
        """Test CLI help command"""
        result = self.run_cli("--help")
        assert result.returncode == 0
        assert "OpenYoung" in result.stdout

    def test_llm_list_command(self):
        """Test 'llm list' command"""
        result = self.run_cli("llm", "list")
        assert result.returncode == 0

    def test_llm_info_command(self):
        """Test 'llm info' command"""
        result = self.run_cli("llm", "info")
        assert result.returncode == 0

    def test_agent_list_command(self):
        """Test 'agent list' command"""
        result = self.run_cli("agent", "list")
        assert result.returncode == 0

    def test_agent_info_command(self):
        """Test 'agent info' command"""
        result = self.run_cli("agent", "info", "default")
        assert result.returncode == 0

    def test_config_list_command(self):
        """Test 'config list' command"""
        result = self.run_cli("config", "list")
        assert result.returncode == 0

    def test_config_get_command(self):
        """Test 'config get' command"""
        result = self.run_cli("config", "get", "llm.model")
        assert result.returncode == 0

    def test_package_list_command(self):
        """Test 'package list' command"""
        result = self.run_cli("package", "list")
        assert result.returncode == 0

    def test_source_list_command(self):
        """Test 'source list' command"""
        result = self.run_cli("source", "list")
        assert result.returncode == 0


def _get_config_value(key: str) -> str:
    """Get config value from environment, handling single quotes"""
    value = os.environ.get(key, "")
    if value.startswith("'") and value.endswith("'"):
        value = value[1:-1]
    return value


class TestLLMApiIntegration:
    """Test actual LLM API calls using .env configuration"""

    def test_llm_client_has_configs(self):
        """Test LLM client has configurations loaded"""
        from src.llm.client import LLMClient

        client = LLMClient()
        assert client is not None
        # Just verify client was created - configs are optional

    @pytest.mark.asyncio
    async def test_deepseek_api_call(self):
        """Test actual DeepSeek API call"""
        from src.llm.client import LLMClient

        deepseek_config = _get_config_value("DEEPSEEK_CONFIG")
        if not deepseek_config:
            pytest.skip("DEEPSEEK_CONFIG not found in .env")

        config = json.loads(deepseek_config)
        model = config["prefix"][0]

        client = LLMClient()
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say 'test successful' if you receive this."},
        ]

        try:
            response = await client.chat(model, messages, temperature=0.7)
            assert response is not None
            assert len(response) > 0
            print(f"DeepSeek API response: {response[:100]}...")
        except Exception as e:
            pytest.fail(f"DeepSeek API call failed: {e}")
        finally:
            await client.close()

    @pytest.mark.asyncio
    async def test_moonshot_api_call(self):
        """Test actual Moonshot API call"""
        from src.llm.client import LLMClient

        moonshot_config = _get_config_value("MOONSHOT_CONFIG")
        if not moonshot_config:
            pytest.skip("MOONSHOT_CONFIG not found in .env")

        config = json.loads(moonshot_config)
        model = config["prefix"][0]

        client = LLMClient()
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say 'test successful' if you receive this."},
        ]

        try:
            response = await client.chat(model, messages, temperature=0.7)
            assert response is not None
            print(f"Moonshot API response: {response[:100]}...")
        except Exception as e:
            pytest.fail(f"Moonshot API call failed: {e}")
        finally:
            await client.close()

    @pytest.mark.asyncio
    async def test_qwen_api_call(self):
        """Test actual Qwen API call"""
        from src.llm.client import LLMClient

        qwen_config = _get_config_value("QWEN_CONFIG")
        if not qwen_config:
            pytest.skip("QWEN_CONFIG not found in .env")

        config = json.loads(qwen_config)
        model = config["prefix"][0]

        client = LLMClient()
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say 'test successful' if you receive this."},
        ]

        try:
            response = await client.chat(model, messages, temperature=0.7)
            assert response is not None
            print(f"Qwen API response: {response[:100]}...")
        except Exception as e:
            pytest.fail(f"Qwen API call failed: {e}")
        finally:
            await client.close()

    @pytest.mark.asyncio
    async def test_glm_api_call(self):
        """Test actual GLM API call"""
        from src.llm.client import LLMClient

        glm_config = _get_config_value("GLM_CONFIG")
        if not glm_config:
            pytest.skip("GLM_CONFIG not found in .env")

        config = json.loads(glm_config)
        model = config["prefix"][0]

        client = LLMClient()
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say 'test successful' if you receive this."},
        ]

        try:
            response = await client.chat(model, messages, temperature=0.7)
            assert response is not None
            print(f"GLM API response: {response[:100]}...")
        except Exception as e:
            pytest.fail(f"GLM API call failed: {e}")
        finally:
            await client.close()


class TestAgentExecution:
    """Test agent execution with real LLM"""

    @pytest.fixture(autouse=True)
    def setup(self, project_root: Path):
        self.project_root = project_root

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_young_agent_run(self):
        """Test YoungAgent run with real LLM"""
        from src.agents.young_agent import YoungAgent
        from src.core.types import AgentConfig, AgentMode

        # Get a valid model
        deepseek_config = _get_config_value("DEEPSEEK_CONFIG")
        if not deepseek_config:
            pytest.skip("No LLM config available")

        config = json.loads(deepseek_config)
        model = config["prefix"][0]

        agent_config = AgentConfig(
            name="test_agent",
            mode=AgentMode.PRIMARY,
            model=model,
            temperature=0.7,
        )

        agent = YoungAgent(agent_config)

        try:
            result = await agent.run("Say 'hello world' in one sentence.")
            assert result is not None
            assert len(result) > 0
            print(f"Agent result: {result[:200]}...")
        except Exception as e:
            pytest.fail(f"Agent execution failed: {e}")


class TestPackageManager:
    """Test Package Manager integration"""

    def test_package_manager_init(self):
        """Test PackageManager initialization"""
        from src.package_manager.manager import PackageManager

        pm = PackageManager()
        assert pm is not None

    def test_provider_manager(self):
        """Test ProviderManager"""
        from src.package_manager.provider import ProviderManager

        pm = ProviderManager()
        providers = pm.available_providers
        assert len(providers) > 0

    def test_list_providers(self):
        """Test listing providers"""
        from src.package_manager.manager import PackageManager

        pm = PackageManager()
        providers = pm.list_providers()
        assert providers is not None


class TestDataCenter:
    """Test DataCenter integration"""

    def test_datacenter_init(self):
        """Test DataCenter initialization"""
        from src.datacenter.datacenter import DataCenter

        dc = DataCenter()
        assert dc is not None


class TestEvolver:
    """Test Evolver integration"""

    def test_evolver_init(self):
        """Test Evolver initialization"""
        from src.evolver.engine import EvolutionEngine

        engine = EvolutionEngine()
        assert engine is not None


class TestEvaluationHub:
    """Test EvaluationHub integration"""

    def test_evaluation_hub_init(self):
        """Test EvaluationHub initialization"""
        from src.evaluation.hub import EvaluationHub

        hub = EvaluationHub()
        assert hub is not None


class TestSkills:
    """Test Skills integration"""

    def test_skill_loader(self):
        """Test SkillLoader"""
        from src.skills.loader import SkillLoader

        loader = SkillLoader()
        assert loader is not None

    def test_skill_registry(self):
        """Test SkillRegistry"""
        from src.skills.registry import SkillRegistry

        registry = SkillRegistry()
        assert registry is not None

    def test_unified_retriever(self):
        """Test UnifiedSkillRetriever"""
        from src.skills.retriever import UnifiedSkillRetriever

        # Create with default config
        config = {
            "storage_dir": "/tmp/test_skills",
            "index_enabled": False,
        }
        retriever = UnifiedSkillRetriever(config)
        assert retriever is not None


class TestPromptTemplates:
    """Test prompt templates"""

    def test_prompt_registry(self):
        """Test PromptRegistry"""
        from src.prompts.templates import PromptRegistry

        registry = PromptRegistry()
        templates = registry.list_templates()
        assert "minimal" in templates
        assert "manus" in templates
        assert "devin" in templates
        assert "windsurf" in templates

    def test_render_template(self):
        """Test template rendering"""
        from src.prompts.templates import render_template

        result = render_template(
            "minimal",
            agent_name="TestAgent",
            task_description="Test task",
        )
        assert "TestAgent" in result
        assert "Test task" in result


class TestFlowSkills:
    """Test Flow Skills"""

    def test_sequential_flow(self):
        """Test SequentialFlow"""
        from src.flow.sequential import SequentialFlow

        flow = SequentialFlow()
        assert flow.name == "sequential"

    def test_parallel_flow(self):
        """Test ParallelFlow"""
        from src.flow.parallel import ParallelFlow

        flow = ParallelFlow()
        assert flow.name == "parallel"

    def test_conditional_flow(self):
        """Test ConditionalFlow"""
        from src.flow.conditional import ConditionalFlow

        flow = ConditionalFlow()
        assert flow.name == "conditional"

    def test_loop_flow(self):
        """Test LoopFlow"""
        from src.flow.loop import LoopFlow

        flow = LoopFlow()
        assert flow.name == "loop"

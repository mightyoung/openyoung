"""
Agent Loader - Agent 配置加载模块

从 main.py 提取的 AgentLoader 功能。
"""

from pathlib import Path
from typing import Optional

from src.core.types import (
    AgentConfig,
    AgentMode,
    PermissionAction,
    PermissionConfig,
    PermissionRule,
    SubAgentConfig,
    SubAgentType,
)


class AgentLoader:
    """Agent 配置加载器"""

    def __init__(self, agent_dir: Optional[str] = None):
        self.agent_dir = Path(agent_dir) if agent_dir else Path(__file__).parent.parent / "agents"
        self.agent_dir.mkdir(parents=True, exist_ok=True)

    def load_agent(self, name: str) -> AgentConfig:
        """加载 Agent 配置 - 支持多个目录"""
        # 1. 直接文件路径
        if Path(name).exists() and Path(name).is_file():
            return self._load_from_file(Path(name))

        # 2. src/agents/ 目录
        agent_file = self.agent_dir / f"{name}.yaml"
        if agent_file.exists():
            return self._load_from_file(agent_file)

        # 3. packages/ 目录 (agent-xxx/agent.yaml 或 xxx/agent.yaml)
        packages_dir = Path("packages")
        if packages_dir.exists():
            for item in packages_dir.iterdir():
                if item.is_dir():
                    yaml_file = item / "agent.yaml"
                    if yaml_file.exists():
                        # 检查是否匹配: agent-role -> role, role -> role
                        if item.name == f"agent-{name}" or item.name == name:
                            return self._load_from_file(yaml_file)

        if name == "default":
            return self._get_default_config()

        raise ValueError(f"Agent not found: {name}")

    def load_subagent(self, name: str) -> AgentConfig:
        """加载 SubAgent 配置"""
        subagents_dir = Path("subagents")
        agent_file = subagents_dir / name / "agent.yaml"
        if agent_file.exists():
            return self._load_from_file(agent_file)
        raise ValueError(f"SubAgent not found: {name}")

    def _load_from_file(self, path: Path) -> AgentConfig:
        try:
            import yaml

            with open(path) as f:
                config = yaml.safe_load(f)
            return self._parse_config(config)
        except ImportError:
            return self._get_default_config()

    def _get_default_config(self) -> AgentConfig:
        return AgentConfig(
            name="default",
            mode=AgentMode.PRIMARY,
            model="deepseek-chat",
            temperature=0.7,
        )

    def _parse_config(self, config: dict) -> AgentConfig:
        """解析完整配置 - 支持两种 model 格式: 字符串或字典"""
        # 处理 model 字段 - 可能是字符串或字典
        model_value = config.get("model", "deepseek-chat")
        if isinstance(model_value, str):
            # 简单格式: model: "deepseek-chat"
            model_name = model_value
            model_config = {}
        else:
            # 复杂格式: model: { name: "...", temperature: 0.7 }
            model_name = model_value.get("name", model_value.get("model", "deepseek-chat"))
            model_config = model_value

        permission_config = config.get("permission", {})
        execution_config = config.get("execution", {})

        # 解析 permission
        permission = self._parse_permission(permission_config)

        # 解析 sub_agents
        sub_agents = self._parse_sub_agents(config.get("sub_agents", []))

        # 解析 system_prompt (支持多行字符串)
        system_prompt = config.get("system_prompt")
        if not system_prompt:
            system_prompt = "你是一个有帮助的AI助手。"

        return AgentConfig(
            name=config.get("name", "unknown"),
            mode=AgentMode.PRIMARY,
            model=model_name,
            temperature=model_config.get("temperature", 0.7),
            max_tokens=model_config.get("max_tokens"),
            tools=config.get("tools", []),
            permission=permission,
            skills=config.get("skills", []),
            always_skills=config.get("always_skills", []),
            sub_agents=sub_agents,
            system_prompt=system_prompt,
            execution=execution_config,
        )

    def _parse_permission(self, config: dict) -> PermissionConfig:
        """解析权限配置 - 参考 OpenCode PermissionNext"""
        # 解析全局默认
        global_action = config.get("_global", "ask")
        if isinstance(global_action, str):
            global_action = PermissionAction(global_action)

        # 解析规则
        rules = []
        for rule in config.get("rules", []):
            tool_pattern = rule.get("tool", "*")
            action_str = rule.get("action", "ask")
            action = PermissionAction(action_str) if isinstance(action_str, str) else action_str
            rules.append(PermissionRule(tool_pattern=tool_pattern, action=action))

        return PermissionConfig(
            _global=global_action,
            rules=rules,
            confirm_message=config.get("confirm_message", "确认执行此操作?"),
        )

    def _parse_sub_agents(self, config: list) -> list[SubAgentConfig]:
        """解析 SubAgent 配置 - 参考 Claude Code Task 协议"""
        sub_agents = []
        for item in config:
            try:
                sub_type = SubAgentType(item.get("type", "general"))
            except ValueError:
                sub_type = SubAgentType.GENERAL

            sub_agents.append(
                SubAgentConfig(
                    name=item.get("name", sub_type.value),
                    type=sub_type,
                    description=item.get("description", ""),
                    model=item.get("model", "deepseek-chat"),
                    temperature=item.get("temperature", 0.7),
                    instructions=item.get("instructions"),
                    hidden=item.get("hidden", False),
                )
            )

        return sub_agents

    def list_agents(self) -> list[str]:
        agents = []

        # 1. 从 src/agents/ 目录扫描
        if self.agent_dir.exists():
            for f in self.agent_dir.glob("*.yaml"):
                agents.append(f.stem)

        # 2. 从 packages/ 目录扫描 (agent-xxx/agent.yaml 或 xxx/agent.yaml)
        packages_dir = Path("packages")
        if packages_dir.exists():
            for item in packages_dir.iterdir():
                if item.is_dir():
                    # 检查 agent.yaml 或 agent-*.yaml
                    yaml_file = item / "agent.yaml"
                    if yaml_file.exists():
                        # 提取 agent 名称: agent-coder -> coder, my-agent -> my-agent
                        name = item.name
                        if name.startswith("agent-"):
                            name = name[6:]  # 去掉 "agent-" 前缀
                        if name not in agents:
                            agents.append(name)

        # 确保 default 在列表中
        if "default" not in agents:
            agents.insert(0, "default")

        return agents

    def list_subagents(self) -> list[str]:
        """列出所有 subagents"""
        subagents = []
        subagents_dir = Path("subagents")
        if subagents_dir.exists():
            for f in subagents_dir.glob("*/agent.yaml"):
                name = f.parent.name
                if name not in subagents:
                    subagents.append(name)
        return sorted(subagents)

    def validate_config(self, config: AgentConfig) -> tuple[bool, str]:
        """Validate Agent configuration

        Returns:
            (is_valid, error_message)
        """
        # Check model is specified
        if not config.model:
            return False, "Model is required"

        # Check temperature is in valid range
        if config.temperature is not None:
            if not 0 <= config.temperature <= 2:
                return False, "Temperature must be between 0 and 2"

        # Check max_tokens is reasonable
        if config.max_tokens is not None:
            if config.max_tokens <= 0:
                return False, "max_tokens must be positive"
            if config.max_tokens > 100000:
                return False, "max_tokens exceeds maximum (100000)"

        # Check mode is valid
        if config.mode not in [AgentMode.PRIMARY, AgentMode.SUBAGENT, AgentMode.ALL]:
            return False, f"Invalid agent mode: {config.mode}"

        return True, ""

    def validate_agent_file(self, path: Path) -> tuple[bool, str]:
        """Validate an agent YAML file before loading

        Returns:
            (is_valid, error_message)
        """
        try:
            import yaml

            with open(path) as f:
                config = yaml.safe_load(f)

            if not config:
                return False, "Empty configuration file"

            # Check required fields
            if "name" not in config:
                return False, "Missing required field: name"

            # Validate model section
            model_config = config.get("model", {})
            if model_config:
                if "model" in model_config:
                    model = model_config["model"]
                    if not isinstance(model, str) or not model.strip():
                        return False, "Invalid model name"

                if "temperature" in model_config:
                    temp = model_config["temperature"]
                    if not isinstance(temp, (int, float)) or not 0 <= temp <= 2:
                        return False, "Temperature must be between 0 and 2"

            return True, ""

        except ImportError:
            return True, ""  # YAML not available, skip validation
        except Exception as e:
            return False, f"Validation error: {str(e)}"

    def load_default(self) -> AgentConfig:
        """Load default agent configuration"""
        return self._get_default_config()

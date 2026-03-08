OpenYoung CLI - 命令行入口

## Classes

### `AgentLoader`

Agent 配置加载器

**Methods:**
- `load_agent`
- `list_agents`
- `validate_config`
- `validate_agent_file`
- `load_default`

### `AgentRunner`

**Methods:**
- `load_agent`

## Functions

### `cli()`

OpenYoung - AI Agent Platform

### `run()`

Run an agent with a task

### `agent()`

Agent management

### `agent_list()`

List available agents

### `agent_info()`

Show agent details

### `agent_use()`

Set default agent

### `agent_search()`

Search agents by keyword, with optional intent analysis

### `agent_intent()`

Analyze user intent and recommend agents

### `agent_evaluate()`

Evaluate agent quality

### `agent_stats()`

Show agent usage statistics

### `agent_compare()`

Compare two agents

### `agent_versions()`

Show agent version history

### `agent_version_add()`

Add a new version for an agent

### `agent_version_check()`

Check if there's a newer version available

### `install()`

Install a package

### `package()`

Package management

### `package_list()`

List available agents (from packages/)

### `package_install()`

Install agent dependencies (via pip)

### `package_create()`

Create a new agent from template

### `llm()`

LLM Provider management

### `llm_list()`

List available LLM providers

### `llm_add()`

Add an LLM provider

### `llm_remove()`

Remove an LLM provider

### `llm_use()`

Set default LLM provider

### `llm_info()`

Show provider details

### `config()`

Configuration management

### `config_list()`

List all configuration settings

### `config_get()`

Get a configuration value

### `config_set()`

Set a configuration value

### `eval()`

Evaluation history and trends

### `eval_history()`

Show evaluation history for an agent

### `eval_trend()`

Show evaluation trend for an agent

### `source()`

Source/package repository management

### `source_list()`

List configured sources

### `source_add()`

Add a new source

### `init()`

Initialize OpenYoung configuration

Interactive wizard to set up:
- LLM Provider selection and API keys
- Default channel configuration
- Agent settings

Example:
    openyoung init
    openyoung init --force

### `channel()`

Channel management

### `channel_list()`

List available channels

### `channel_config_cmd()`

Configure channels

Actions:
    show              - Show current channel configuration
    add <platform>   - Add a channel (telegram/discord/dingtalk/feishu/qq)
    remove <platform> - Remove a channel
    enable <platform> - Enable a channel
    disable <platform> - Disable a channel

Examples:
    openyoung channel config show
    openyoung channel config add feishu --app-id xxx --app-secret xxx
    openyoung channel config enable telegram
    openyoung channel config disable dingtalk

### `channel_start()`

Start a channel server

Examples:
    openyoung channel start
    openyoung channel start feishu
    openyoung channel start feishu --port 3000

### `import_cmd()`

Import from external sources

### `import_github()`

Import agent from GitHub URL

Example:
    openyoung import github https://github.com/affaan-m/everything-claude-code my-agent
    openyoung import github https://github.com/anthropics/claude-code claude-code --no-lazy

### `subagent()`

SubAgent management

### `subagent_list()`

List all subagents

### `subagent_info()`

Show subagent details

### `mcp()`

MCP Server management

### `mcp_servers()`

List available MCP servers

### `mcp_start()`

Start an MCP server

### `mcp_stop()`

Stop an MCP server

### `templates()`

Template marketplace commands

### `templates_list()`

List available templates

### `templates_search()`

Search templates

### `templates_add()`

Add a template to the registry

### `templates_remove()`

Remove a template from the registry

### `templates_info()`

Show template details

### `memory()`

Memory and vector search commands

### `memory_search()`

Search memory using semantic vector search

### `memory_stats()`

Show memory statistics

### `run_agent()`

Run an agent

Examples:
    openyoung run default "Hello"
    openyoung run default -i
    openyoung run default --github https://github.com/user/repo "analyze this"

### `data()`

Data management commands

### `data_stats()`

Show run statistics

### `data_runs()`

List recent runs

### `data_export()`

Export data to directory

### `data_dashboard()`

Show dashboard data

### `data_steps()`

List steps for a run

### `data_license()`

Manage data licenses

### `data_team()`

Manage teams

### `data_access()`

Log data access

### `main()`

### `load_agent()`

加载 Agent 配置 - 支持多个目录

### `list_agents()`

### `validate_config()`

Validate Agent configuration

Returns:
    (is_valid, error_message)

### `validate_agent_file()`

Validate an agent YAML file before loading

Returns:
    (is_valid, error_message)

### `load_default()`

Load default agent configuration

### `load_agent()`

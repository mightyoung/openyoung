Dependency Resolver - Agent 依赖解析器
解析 Agent 配置中的 Skills/MCPs/Hooks 依赖

## Classes

### `DependencyInfo`

依赖信息

### `AgentDependency`

Agent 依赖

**Methods:**
- `all_dependencies`
- `required_dependencies`
- `optional_dependencies`

### `DependencyResolver`

依赖解析器

**Methods:**
- `resolve_from_config`
- `resolve_from_file`
- `check_installed`
- `find_missing`

## Functions

### `resolve_agent_dependencies()`

解析 Agent 依赖，返回 (all, missing)

Args:
    agent_path: Agent 配置目录路径

Returns:
    (所有依赖, 缺失的依赖)

### `all_dependencies()`

所有依赖

### `required_dependencies()`

必需的依赖

### `optional_dependencies()`

可选的依赖

### `resolve_from_config()`

从配置解析依赖

支持的配置格式：
- required_skills: ["skill-github-import", ...]
- required_mcps: ["mcp-github", ...]
- required_hooks: ["hooks-auto-commit", ...]

### `resolve_from_file()`

从文件解析依赖

### `check_installed()`

检查依赖是否已安装

### `find_missing()`

找出缺失的依赖

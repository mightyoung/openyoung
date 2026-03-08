MCP Server Manager
MCP Server 管理器 - 支持先决加载和动态启动
支持连接检测 + 智能启动 + 失败跳过

## Classes

### `MCPServerConfig`

MCP Server 配置

### `MCPConnectionResult`

MCP 连接检测结果

### `MCPServerManager`

MCP Server 管理器

**Methods:**
- `discover_mcp_servers`
- `check_and_start_mcp`
- `load_required_mcps`
- `load_required_mcps_fast`
- `start_mcp_server`

### `AgentMCPLoader`

Agent MCP 加载器 - 确保 Agent 加载前 MCP 已启动

智能加载流程:
1. 检查 MCP 是否已运行 -> 已运行则跳过
2. 尝试 MCP 协议检测连接 -> 可连接则跳过
3. 尝试启动 MCP Server -> 启动成功则继续
4. 启动失败 -> 跳过继续执行 (不报错)

**Methods:**
- `load_agent_with_mcps`
- `load_agent_with_mcps_strict`
- `cleanup`

## Functions

### `load_agent_with_mcps()`

CLI 入口 - 加载 Agent 并先决启动 MCP (智能跳过模式)

### `load_agent_with_mcps_strict()`

CLI 入口 - 加载 Agent 并先决启动 MCP (严格模式)

### `discover_mcp_servers()`

发现所有 MCP Server 配置

### `check_and_start_mcp()`

检查 MCP 连接状态，如未连接则尝试启动，失败则跳过

流程:
1. 检查进程是否已运行 -> 已运行则返回 connected
2. 尝试通过 MCP 协议检测连接 -> 可连接则返回 connected
3. 尝试启动 MCP Server -> 启动成功则返回 connected
4. 启动失败 -> 返回 not connected 但不报错，继续下一步

### `load_required_mcps()`

加载所需的 MCP Servers (先决加载 + 智能跳过)

### `load_required_mcps_fast()`

快速加载 - 返回简单布尔结果

### `start_mcp_server()`

启动 MCP Server

### `load_agent_with_mcps()`

加载 Agent 并先决启动所需 MCP (智能跳过模式)

### `load_agent_with_mcps_strict()`

严格模式 - MCP 失败则报错 (保留兼容)

### `cleanup()`

清理 - 停止所有 MCP Servers

"""
MCP Server Manager
MCP Server 管理器 - 支持先决加载和动态启动
支持连接检测 + 智能启动 + 失败跳过
"""

import json
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class MCPServerConfig:
    """MCP Server 配置"""
    name: str
    command: str
    args: list[str] = None
    env: dict[str, str] = None
    auto_start: bool = True
    check_command: str = None


@dataclass
class MCPConnectionResult:
    """MCP 连接检测结果"""
    mcp_name: str
    is_connected: bool
    needs_start: bool
    start_success: bool
    error: str = ""


class MCPServerManager:
    """MCP Server 管理器"""

    def __init__(self, packages_dir: str = "packages"):
        self.packages_dir = Path(packages_dir)
        self.running_servers: dict[str, subprocess.Popen] = {}
        self.server_configs: dict[str, MCPServerConfig] = {}

    def discover_mcp_servers(self) -> dict[str, list[MCPServerConfig]]:
        """发现所有 MCP Server 配置"""
        servers = {}

        if not self.packages_dir.exists():
            return servers

        for item in self.packages_dir.iterdir():
            if not item.is_dir():
                continue

            # 查找 mcp.json
            mcp_json = item / "mcp.json"
            if mcp_json.exists():
                try:
                    config = json.loads(mcp_json.read_text(encoding="utf-8"))
                    mcp_servers = config.get("mcpServers", {})

                    for name, server_config in mcp_servers.items():
                        cmd = server_config.get("command", "")
                        args = server_config.get("args", [])
                        env = server_config.get("env", {})

                        servers[name] = MCPServerConfig(
                            name=name,
                            command=cmd,
                            args=args,
                            env=env,
                        )
                except Exception as e:
                    print(f"[Warning] Failed to parse mcp.json in {item.name}: {e}")

        return servers

    def check_and_start_mcp(self, mcp_name: str) -> MCPConnectionResult:
        """检查 MCP 连接状态，如未连接则尝试启动，失败则跳过

        流程:
        1. 检查进程是否已运行 -> 已运行则返回 connected
        2. 尝试通过 MCP 协议检测连接 -> 可连接则返回 connected
        3. 尝试启动 MCP Server -> 启动成功则返回 connected
        4. 启动失败 -> 返回 not connected 但不报错，继续下一步
        """
        # Step 1: 检查进程是否已运行
        if mcp_name in self.running_servers:
            proc = self.running_servers[mcp_name]
            if proc.poll() is None:
                return MCPConnectionResult(
                    mcp_name=mcp_name,
                    is_connected=True,
                    needs_start=False,
                    start_success=True,
                )

        # Step 2: 尝试 MCP 协议检测连接
        if self._probe_mcp_connection(mcp_name):
            return MCPConnectionResult(
                mcp_name=mcp_name,
                is_connected=True,
                needs_start=False,
                start_success=True,
            )

        # Step 3: 尝试启动 MCP Server
        print(f"[MCP] {mcp_name} not connected, attempting to start...")
        start_success = self.start_mcp_server(mcp_name)

        if start_success:
            # 再次检测连接
            time.sleep(1)  # 等待启动
            if self._probe_mcp_connection(mcp_name):
                return MCPConnectionResult(
                    mcp_name=mcp_name,
                    is_connected=True,
                    needs_start=True,
                    start_success=True,
                )

        # Step 4: 启动失败，跳过继续执行
        print(f"[MCP] {mcp_name} failed to start, skipping...")
        return MCPConnectionResult(
            mcp_name=mcp_name,
            is_connected=False,
            needs_start=True,
            start_success=False,
            error="Failed to start MCP server, skipping",
        )

    def _probe_mcp_connection(self, mcp_name: str) -> bool:
        """通过 MCP 协议探测连接

        使用 MCP JSON-RPC 协议发送 initialize 请求
        """
        try:
            # 查找配置文件获取连接信息
            all_servers = self.discover_mcp_servers()
            server_config = None

            for servers in all_servers.values():
                for s in servers:
                    if s.name == mcp_name:
                        server_config = s
                        break
                if server_config:
                    break

            if not server_config:
                return False

            # 尝试通过 stdio 连接检测
            # MCP 协议使用 JSON-RPC over stdio
            import json

            # 构建 MCP initialize 请求
            mcp_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "openyoung",
                        "version": "1.0.0"
                    }
                }
            }

            # 通过 stdio 发送请求检测
            cmd = [server_config.command] + (server_config.args or [])
            env = {}
            if server_config.env:
                env.update(server_config.env)
            env["PATH"] = subprocess.os.environ.get("PATH", "")

            proc = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                text=True,
            )

            # 发送请求
            request_str = json.dumps(mcp_request) + "\n"
            try:
                stdout, stderr = proc.communicate(input=request_str, timeout=3)
                proc.wait(timeout=1)

                # 检查是否有有效响应
                if stdout and "jsonrpc" in stdout:
                    return True
            except subprocess.TimeoutExpired:
                proc.kill()
                # 超时可能表示 server 在运行但无响应，也算连接成功
                return proc.poll() is None

            return False

        except Exception:
            # 连接检测失败，不报错
            return False

    def load_required_mcps(self, mcp_list: list[str]) -> dict[str, MCPConnectionResult]:
        """加载所需的 MCP Servers (先决加载 + 智能跳过)"""
        results = {}

        for mcp_name in mcp_list:
            results[mcp_name] = self.check_and_start_mcp(mcp_name)

        return results

    def load_required_mcps_fast(self, mcp_list: list[str]) -> dict[str, bool]:
        """快速加载 - 返回简单布尔结果"""
        results = {}
        for mcp_name in mcp_list:
            result = self.check_and_start_mcp(mcp_name)
            results[mcp_name] = result.is_connected
        return results

    def start_mcp_server(self, mcp_name: str) -> bool:
        """启动 MCP Server"""
        # 如果已经运行，不重复启动
        if mcp_name in self.running_servers:
            proc = self.running_servers[mcp_name]
            if proc.poll() is None:
                return True

        # 查找配置
        all_servers = self.discover_mcp_servers()
        server_config = None

        for servers in all_servers.values():
            for s in servers:
                if s.name == mcp_name:
                    server_config = s
                    break
            if server_config:
                break

        if not server_config:
            print(f"[Warning] MCP Server config not found: {mcp_name}")
            return False

        # 启动 Server
        try:
            cmd = [server_config.command] + (server_config.args or [])

            env = {}
            if server_config.env:
                env.update(server_config.env)
            env.update({"PATH": subprocess.os.environ.get("PATH", "")})

            proc = subprocess.Popen(
                cmd,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            self.running_servers[mcp_name] = proc
            print(f"[MCP] Started server: {mcp_name} (PID: {proc.pid})")

            # 等待 Server 启动
            time.sleep(1)

            return proc.poll() is None

        except Exception as e:
            print(f"[Error] Failed to start MCP Server {mcp_name}: {e}")
            return False


class AgentMCPLoader:
    """Agent MCP 加载器 - 确保 Agent 加载前 MCP 已启动

    智能加载流程:
    1. 检查 MCP 是否已运行 -> 已运行则跳过
    2. 尝试 MCP 协议检测连接 -> 可连接则跳过
    3. 尝试启动 MCP Server -> 启动成功则继续
    4. 启动失败 -> 跳过继续执行 (不报错)
    """

    def __init__(self, packages_dir: str = "packages"):
        self.manager = MCPServerManager(packages_dir)

    def load_agent_with_mcps(self, agent_config: dict[str, Any]) -> dict[str, Any]:
        """加载 Agent 并先决启动所需 MCP (智能跳过模式)"""
        # 获取 Agent 所需的 MCPs
        required_mcps = agent_config.get("mcps", [])

        if not required_mcps:
            return {
                "status": "no_mcps_required",
                "agent": agent_config,
                "mcp_results": {},
            }

        # 智能加载 MCPs (检测 + 启动 + 失败跳过)
        mcp_results = self.manager.load_required_mcps(required_mcps)

        # 统计结果
        connected = [r.mcp_name for r in mcp_results.values() if r.is_connected]
        skipped = [r.mcp_name for r in mcp_results.values() if not r.is_connected and not r.start_success]

        if skipped:
            print(f"[MCP] {len(skipped)} MCP(s) skipped due to connection failure: {skipped}")

        return {
            "status": "success",  # 即使有失败也返回 success，因为会跳过
            "agent": agent_config,
            "mcp_results": {
                name: {
                    "is_connected": result.is_connected,
                    "needs_start": result.needs_start,
                    "start_success": result.start_success,
                    "error": result.error,
                }
                for name, result in mcp_results.items()
            },
            "connected_mcps": connected,
            "skipped_mcps": skipped,
            "running_mcps": self.manager.get_running_servers(),
        }

    def load_agent_with_mcps_strict(self, agent_config: dict[str, Any]) -> dict[str, Any]:
        """严格模式 - MCP 失败则报错 (保留兼容)"""
        required_mcps = agent_config.get("mcps", [])

        if not required_mcps:
            return {"status": "no_mcps_required", "agent": agent_config}

        mcp_results = self.manager.load_required_mcps(required_mcps)
        failed_mcps = [r.mcp_name for r in mcp_results.values() if not r.is_connected]

        if failed_mcps:
            return {
                "status": "mcp_failure",
                "agent": agent_config,
                "failed_mcps": failed_mcps,
                "error": f"MCP(s) failed to connect: {failed_mcps}",
            }

        return {
            "status": "success",
            "agent": agent_config,
            "running_mcps": self.manager.get_running_servers(),
        }

    def cleanup(self):
        """清理 - 停止所有 MCP Servers"""
        self.manager.stop_all_servers()


def load_agent_with_mcps(agent_config: dict[str, Any], packages_dir: str = "packages") -> dict[str, Any]:
    """CLI 入口 - 加载 Agent 并先决启动 MCP (智能跳过模式)"""
    loader = AgentMCPLoader(packages_dir)
    return loader.load_agent_with_mcps(agent_config)


def load_agent_with_mcps_strict(agent_config: dict[str, Any], packages_dir: str = "packages") -> dict[str, Any]:
    """CLI 入口 - 加载 Agent 并先决启动 MCP (严格模式)"""
    loader = AgentMCPLoader(packages_dir)
    return loader.load_agent_with_mcps_strict(agent_config)

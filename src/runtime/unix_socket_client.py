"""
Unix Socket IPC Client for Sandbox Sidecar

Provides fast communication with Rust sandbox service via Unix Domain Socket
instead of gRPC for lower latency.
"""

import json
import os
import socket
from typing import Any, Dict


class UnixSocketClient:
    """Unix Domain Socket client for sandbox execution"""

    def __init__(self, socket_path: str = None):
        # Use environment variable or default
        self.socket_path = socket_path or os.environ.get(
            "IRONCLAW_SOCKET", "/tmp/ironclaw-sandbox.sock"
        )

    def _send_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Send request and receive response via Unix socket"""
        # Don't delete the socket file - it's created by the server
        # Only attempt to remove if connection fails with ECONNREFUSED
        # (meaning no server is listening)

        client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            client.connect(self.socket_path)

            # Send request
            request_json = json.dumps(request) + "\n"
            client.sendall(request_json.encode("utf-8"))

            # Receive response
            response_data = b""
            while True:
                chunk = client.recv(4096)
                if not chunk:
                    break
                response_data += chunk
                # Check if we have complete JSON
                try:
                    response = json.loads(response_data.decode("utf-8"))
                    return response
                except json.JSONDecodeError:
                    continue

            # Try to parse what we have
            return json.loads(response_data.decode("utf-8"))
        finally:
            client.close()

    def execute(self, command: str, timeout_secs: int = 120) -> Dict[str, Any]:
        """Execute command in sandbox"""
        request = {
            "action": "execute",
            "command": command,
            "timeout_secs": timeout_secs,
        }
        return self._send_request(request)

    def health_check(self) -> bool:
        """Check if sandbox service is healthy"""
        request = {"action": "health"}
        try:
            response = self._send_request(request)
            return response.get("status") == "ok"
        except Exception:
            return False

    def configure(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Configure sandbox policy"""
        request = {
            "action": "configure",
            "config": config,
        }
        return self._send_request(request)


class SandboxSidecar:
    """High-level sandbox wrapper with Unix socket IPC"""

    def __init__(
        self,
        socket_path: str = None,
        policy: str = "readonly",
        memory_limit_mb: int = 2048,
        cpu_shares: int = 1024,
    ):
        # Use environment variable or default
        socket_path = socket_path or os.environ.get("IRONCLAW_SOCKET", "/tmp/ironclaw-sandbox.sock")
        self.client = UnixSocketClient(socket_path)
        self.policy = policy
        self.memory_limit_mb = memory_limit_mb
        self.cpu_shares = cpu_shares

    def _ensure_configured(self):
        """Configure sandbox if not already configured"""
        config = {
            "policy": self.policy,
            "memory_limit_mb": self.memory_limit_mb,
            "cpu_shares": self.cpu_shares,
        }
        return self.client.configure(config)

    def execute(self, command: str, timeout_secs: int = 120) -> Dict[str, Any]:
        """Execute command in sandbox"""
        # Try to configure first (idempotent)
        try:
            self._ensure_configured()
        except Exception as e:
            logger.debug(f"Sandbox already configured or configuration failed: {e}")

        return self.client.execute(command, timeout_secs)

    def is_healthy(self) -> bool:
        """Check if sandbox service is running"""
        return self.client.health_check()


# Convenience function
def create_sandbox_sidecar(
    socket_path: str = None,
    policy: str = "readonly",
) -> SandboxSidecar:
    """Create a sandbox sidecar instance"""
    socket_path = socket_path or os.environ.get("IRONCLAW_SOCKET", "/tmp/ironclaw-sandbox.sock")
    return SandboxSidecar(socket_path=socket_path, policy=policy)


if __name__ == "__main__":
    # Test the client
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m src.runtime.unix_socket_client <command>")
        sys.exit(1)

    command = " ".join(sys.argv[1:])
    client = UnixSocketClient()

    print(f"Executing: {command}")
    result = client.execute(command)

    print(f"Status: {result.get('status')}")
    print(f"Exit code: {result.get('exit_code')}")
    print(f"Output:\n{result.get('output', result.get('error'))}")

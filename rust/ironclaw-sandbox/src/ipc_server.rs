//!
//! Unix Socket IPC Server for Sandbox Sidecar
//!
//! Uses Unix Domain Sockets for faster inter-process communication
//! compared to TCP/gRPC.
//!
//! Protocol: Simple JSON messages over Unix socket
//! - Client sends: {"action": "execute", "command": "...", "config": {...}}
//! - Server responds: {"status": "ok", "output": "...", "exit_code": 0}
//!

use std::path::PathBuf;
use std::os::unix::fs::PermissionsExt;
use std::os::unix::net::{UnixListener, UnixStream};
use std::io::{Read, Write, BufRead, BufReader};
use std::process::{Command, Stdio};
use std::sync::{Arc, Mutex};
use std::collections::HashMap;
use std::thread;

use serde::{Deserialize, Serialize};
use tracing::{info, error};

/// Request from Python client
#[derive(Debug, Deserialize)]
pub struct IpcRequest {
    pub action: String,
    pub command: Option<String>,
    pub config: Option<SandboxConfig>,
    pub timeout_secs: Option<u64>,
}

/// Response to Python client
#[derive(Debug, Serialize)]
pub struct IpcResponse {
    pub status: String,
    pub output: Option<String>,
    pub error: Option<String>,
    pub exit_code: Option<i32>,
    pub execution_time_ms: Option<u64>,
}

/// Sandbox configuration
#[derive(Debug, Deserialize, Clone)]
pub struct SandboxConfig {
    pub policy: String,
    pub memory_limit_mb: Option<u64>,
    pub cpu_shares: Option<u32>,
    pub allowed_domains: Option<Vec<String>>,
    pub env_vars: Option<HashMap<String, String>>,
}

impl Default for SandboxConfig {
    fn default() -> Self {
        Self {
            policy: "readonly".to_string(),
            memory_limit_mb: Some(2048),
            cpu_shares: Some(1024),
            allowed_domains: None,
            env_vars: None,
        }
    }
}

/// Sandbox executor using Docker
pub struct SandboxExecutor {
    config: SandboxConfig,
}

impl SandboxExecutor {
    pub fn new(config: SandboxConfig) -> Self {
        Self { config }
    }

    /// Execute command in sandbox
    pub fn execute(&self, command: &str, timeout_secs: u64) -> IpcResponse {
        let start = std::time::Instant::now();

        // Build docker command based on policy
        let mut cmd = Command::new("docker");
        cmd.args([
            "run", "--rm",
            "--network", "none",  // Network isolation by default
            "--memory", &format!("{}m", self.config.memory_limit_mb.unwrap_or(2048)),
            "--cpu-shares", &self.config.cpu_shares.unwrap_or(1024).to_string(),
            "--pids-limit", "100",
            "--cap-drop", "ALL",
            "--security-opt", "no-new-privileges",
            "-i",  // Interactive
        ]);

        // Add policy-specific options
        match self.config.policy.as_str() {
            "readonly" => {
                if let Ok(cwd) = std::env::current_dir() {
                    cmd.arg("-v").arg(format!("{}:/workspace:ro", cwd.display()));
                }
            },
            "workspace_write" => {
                if let Ok(cwd) = std::env::current_dir() {
                    cmd.arg("-v").arg(format!("{}:/workspace:rw", cwd.display()));
                }
            },
            "full" => {
                // No restrictions - full access
            },
            _ => {
                if let Ok(cwd) = std::env::current_dir() {
                    cmd.arg("-v").arg(format!("{}:/workspace:ro", cwd.display()));
                }
            }
        }

        // Add environment variables
        if let Some(env_vars) = &self.config.env_vars {
            for (key, value) in env_vars {
                cmd.arg("-e").arg(format!("{}={}", key, value));
            }
        }

        // Use lightweight image
        cmd.arg("alpine:latest")
            .arg("sh")
            .arg("-c")
            .arg(command);

        // Set up pipe for output
        cmd.stdout(Stdio::piped());
        cmd.stderr(Stdio::piped());

        // Execute
        match cmd.output() {
            Ok(output) => {
                let elapsed = start.elapsed().as_millis() as u64;
                let stdout = String::from_utf8_lossy(&output.stdout).to_string();
                let stderr = String::from_utf8_lossy(&output.stderr).to_string();

                let combined_output = if stderr.is_empty() {
                    stdout
                } else {
                    format!("{}\nSTDERR: {}", stdout, stderr)
                };

                IpcResponse {
                    status: "ok".to_string(),
                    output: Some(combined_output),
                    error: None,
                    exit_code: Some(output.status.code().unwrap_or(-1)),
                    execution_time_ms: Some(elapsed),
                }
            },
            Err(e) => {
                let elapsed = start.elapsed().as_millis() as u64;
                IpcResponse {
                    status: "error".to_string(),
                    output: None,
                    error: Some(e.to_string()),
                    exit_code: Some(-1),
                    execution_time_ms: Some(elapsed),
                }
            }
        }
    }
}

/// IPC Server that handles Unix socket connections
pub struct IpcServer {
    socket_path: PathBuf,
    executor: Arc<Mutex<SandboxExecutor>>,
}

impl IpcServer {
    pub fn new(socket_path: &str, executor: SandboxExecutor) -> Self {
        Self {
            socket_path: PathBuf::from(socket_path),
            executor: Arc::new(Mutex::new(executor)),
        }
    }

    /// Start the IPC server
    pub fn start(&self) -> Result<(), Box<dyn std::error::Error>> {
        // Remove existing socket file
        if self.socket_path.exists() {
            std::fs::remove_file(&self.socket_path)?;
        }

        // Create Unix socket listener
        let listener = UnixListener::bind(&self.socket_path)?;

        // Set socket to non-blocking for accept
        listener.set_nonblocking(true)?;

        // Set socket permissions (read/write for owner and group)
        let mut perms = std::fs::metadata(&self.socket_path)?.permissions();
        perms.set_mode(0o660);
        std::fs::set_permissions(&self.socket_path, perms)?;

        info!("IPC server listening on {}", self.socket_path.display());

        // Keep the server running
        loop {
            // Accept connections in a non-blocking loop
            match listener.accept() {
                Ok((mut stream, _addr)) => {
                    let executor = Arc::clone(&self.executor);
                    thread::spawn(move || {
                        if let Err(e) = Self::handle_connection(&mut stream, executor) {
                            error!("Connection error: {}", e);
                        }
                    });
                }
                Err(ref e) if e.kind() == std::io::ErrorKind::WouldBlock => {
                    // No pending connections, sleep briefly
                    std::thread::sleep(std::time::Duration::from_millis(100));
                }
                Err(e) => {
                    error!("Accept error: {}", e);
                    std::thread::sleep(std::time::Duration::from_millis(100));
                }
            }
        }
    }

    /// Handle a single client connection
    fn handle_connection(
        stream: &mut UnixStream,
        executor: Arc<Mutex<SandboxExecutor>>,
    ) -> Result<(), Box<dyn std::error::Error>> {
        let mut reader = BufReader::new(stream.try_clone()?);
        let mut data = String::new();

        // Read request line
        reader.read_line(&mut data)?;
        data = data.trim().to_string();

        // Parse request
        let request: IpcRequest = match serde_json::from_str(&data) {
            Ok(r) => r,
            Err(e) => {
                let response = IpcResponse {
                    status: "error".to_string(),
                    output: None,
                    error: Some(format!("Parse error: {}", e)),
                    exit_code: Some(-1),
                    execution_time_ms: None,
                };
                let response_json = serde_json::to_string(&response)?;
                stream.write_all(response_json.as_bytes())?;
                stream.write_all(b"\n")?;
                return Ok(());
            }
        };

        // Process request
        let response = match request.action.as_str() {
            "execute" => {
                let cmd = request.command.unwrap_or_default();
                let timeout = request.timeout_secs.unwrap_or(120);

                let executor = executor.lock().unwrap();
                executor.execute(&cmd, timeout)
            },
            "health" => {
                IpcResponse {
                    status: "ok".to_string(),
                    output: Some("healthy".to_string()),
                    error: None,
                    exit_code: Some(0),
                    execution_time_ms: Some(0),
                }
            },
            "configure" => {
                // Update configuration
                if let Some(config) = request.config {
                    let mut executor = executor.lock().unwrap();
                    *executor = SandboxExecutor::new(config);
                }
                IpcResponse {
                    status: "ok".to_string(),
                    output: Some("configured".to_string()),
                    error: None,
                    exit_code: Some(0),
                    execution_time_ms: None,
                }
            },
            _ => {
                IpcResponse {
                    status: "error".to_string(),
                    output: None,
                    error: Some(format!("Unknown action: {}", request.action)),
                    exit_code: Some(-1),
                    execution_time_ms: None,
                }
            }
        };

        // Send response
        let response_json = serde_json::to_string(&response)?;
        stream.write_all(response_json.as_bytes())?;
        stream.write_all(b"\n")?;

        Ok(())
    }
}

/// Start the IPC server
pub fn start_server(socket_path: &str, config: SandboxConfig) {
    let executor = SandboxExecutor::new(config);
    let server = IpcServer::new(socket_path, executor);

    if let Err(e) = server.start() {
        error!("Server error: {}", e);
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_sandbox_config_default() {
        let config = SandboxConfig::default();
        assert_eq!(config.policy, "readonly");
        assert_eq!(config.memory_limit_mb, Some(2048));
    }

    #[test]
    fn test_ipc_request_parse() {
        let json = r#"{"action": "execute", "command": "ls -la", "timeout_secs": 30}"#;
        let req: IpcRequest = serde_json::from_str(json).unwrap();
        assert_eq!(req.action, "execute");
        assert_eq!(req.command, Some("ls -la".to_string()));
        assert_eq!(req.timeout_secs, Some(30));
    }
}

//!
//! Simple Unix Socket IPC Server for Sandbox Sidecar
//!

use std::path::PathBuf;
use std::os::unix::net::{UnixListener, UnixStream};
use std::io::{Read, Write};
use std::process::{Command, Stdio};
use std::sync::{Arc, Mutex};
use std::collections::HashMap;
use std::thread;

use serde::{Deserialize, Serialize};
use tracing::{info, error};

#[derive(Debug, Deserialize)]
pub struct IpcRequest {
    pub action: String,
    pub command: Option<String>,
    pub timeout_secs: Option<u64>,
}

#[derive(Debug, Serialize)]
pub struct IpcResponse {
    pub status: String,
    pub output: Option<String>,
    pub error: Option<String>,
    pub exit_code: Option<i32>,
    pub execution_time_ms: Option<u64>,
}

pub fn execute_command(command: &str) -> IpcResponse {
    let start = std::time::Instant::now();

    let output = Command::new("sh")
        .arg("-c")
        .arg(command)
        .output();

    let elapsed = start.elapsed().as_millis() as u64;

    match output {
        Ok(out) => {
            let stdout = String::from_utf8_lossy(&out.stdout).to_string();
            let stderr = String::from_utf8_lossy(&out.stderr).to_string();
            let combined = if stderr.is_empty() { stdout } else { format!("{}\nSTDERR: {}", stdout, stderr) };

            IpcResponse {
                status: "ok".to_string(),
                output: Some(combined),
                error: None,
                exit_code: Some(out.status.code().unwrap_or(-1)),
                execution_time_ms: Some(elapsed),
            }
        },
        Err(e) => {
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

fn handle_client(mut stream: UnixStream) {
    // Set non-blocking for this stream
    stream.set_nonblocking(true).ok();

    let mut buffer = String::new();
    let mut buf = [0u8; 4096];

    // Read the request (non-blocking)
    loop {
        match stream.read(&mut buf) {
            Ok(0) => {
                // Connection closed
                return;
            }
            Ok(n) => {
                buffer.push_str(&String::from_utf8_lossy(&buf[..n]));
            }
            Err(ref e) if e.kind() == std::io::ErrorKind::WouldBlock => {
                // No data available yet, wait a bit and retry
                std::thread::sleep(std::time::Duration::from_millis(10));
                continue;
            }
            Err(e) => {
                error!("Read error: {}", e);
                return;
            }
        }
        // Check if we have complete data (newline terminated)
        if buffer.contains('\n') {
            break;
        }
    }

    buffer = buffer.trim().to_string();
    if buffer.is_empty() {
        return;
    }

    // Parse JSON
    let request: IpcRequest = match serde_json::from_str(&buffer) {
        Ok(r) => r,
        Err(e) => {
            let response = IpcResponse {
                status: "error".to_string(),
                output: None,
                error: Some(format!("Parse error: {}", e)),
                exit_code: Some(-1),
                execution_time_ms: None,
            };
            let _ = stream.write_all(serde_json::to_string(&response).unwrap().as_bytes());
            return;
        }
    };

    // Process request
    let response = match request.action.as_str() {
        "execute" => {
            let cmd = request.command.unwrap_or_else(|| "echo test".to_string());
            execute_command(&cmd)
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
    if let Err(e) = stream.write_all(serde_json::to_string(&response).unwrap().as_bytes()) {
        error!("Write error: {}", e);
    }
}

fn main() {
    tracing_subscriber::fmt()
        .with_target(false)
        .init();

    // Use environment variable or default
    let socket_path = std::env::var("IRONCLAW_SOCKET")
        .unwrap_or_else(|_| "/tmp/ironclaw-sandbox.sock".to_string());

    // Clean up old socket
    if std::path::Path::new(&socket_path).exists() {
        std::fs::remove_file(&socket_path).ok();
    }

    // Create listener
    let listener = UnixListener::bind(&socket_path).expect("Failed to bind socket");

    // Set non-blocking
    listener.set_nonblocking(true).ok();

    info!("IPC server listening on {}", socket_path);

    // Keep running
    loop {
        match listener.accept() {
            Ok((stream, _)) => {
                thread::spawn(|| {
                    handle_client(stream);
                });
            }
            Err(ref e) if e.kind() == std::io::ErrorKind::WouldBlock => {
                std::thread::sleep(std::time::Duration::from_millis(50));
            }
            Err(e) => {
                error!("Accept error: {}", e);
                std::thread::sleep(std::time::Duration::from_millis(50));
            }
        }
    }
}

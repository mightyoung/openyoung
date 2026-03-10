//!
//! Unix Socket IPC Server Main Entry Point
//!
//! Run with: cargo run --bin ironclaw-ipc
//!

use std::env;

mod ipc_server;

fn main() {
    // Initialize logging
    tracing_subscriber::fmt()
        .with_target(false)
        .init();

    let socket_path = env::args()
        .nth(1)
        .unwrap_or_else(|| "/tmp/ironclaw-sandbox.sock".to_string());

    let config = ipc_server::SandboxConfig {
        policy: env::args()
            .nth(2)
            .unwrap_or_else(|| "readonly".to_string()),
        memory_limit_mb: env::args()
            .nth(3)
            .and_then(|s| s.parse().ok()),
        cpu_shares: env::args()
            .nth(4)
            .and_then(|s| s.parse().ok()),
        allowed_domains: None,
        env_vars: None,
    };

    println!("Starting IronClaw Sandbox IPC Server...");
    println!("Socket path: {}", socket_path);
    println!("Policy: {}", config.policy);

    ipc_server::start_server(&socket_path, config);
}

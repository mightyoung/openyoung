//! Full Observability Audit Module
//!
//! Records complete execution context for debugging and analysis

use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::fs::{File, OpenOptions};
use std::io::Write;
use std::path::PathBuf;
use std::sync::Mutex;
use chrono::{DateTime, Utc};

/// Agent skill information
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SkillInfo {
    pub name: String,
    pub path: String,
    pub version: Option<String>,
    pub enabled: bool,
}

/// MCP server configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct McpInfo {
    pub name: String,
    pub command: String,
    pub args: Vec<String>,
    pub env: HashMap<String, String>,
}

/// Hook configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HookInfo {
    pub name: String,
    pub hook_type: String,
    pub enabled: bool,
    pub last_executed: Option<DateTime<Utc>>,
    pub result: Option<String>,
}

/// Network connection status
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct NetworkStatus {
    pub connected: bool,
    pub connections: Vec<ConnectionInfo>,
}

/// External connection details
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ConnectionInfo {
    pub target: String,
    pub port: Option<u16>,
    pub protocol: String,
    pub status: String,
    pub bytes_sent: u64,
    pub bytes_received: u64,
}

/// Sub-agent execution record
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SubAgentExecution {
    pub agent_id: String,
    pub agent_name: String,
    pub task: String,
    pub start_time: DateTime<Utc>,
    pub end_time: Option<DateTime<Utc>>,
    pub status: String,
    pub result: Option<String>,
    pub iterations: u32,
}

/// Evaluation result
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EvaluationResult {
    pub metric: String,
    pub score: f64,
    pub reasoning: String,
    pub timestamp: DateTime<Utc>,
}

/// Iteration record for self-improvement loops
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct IterationRecord {
    pub iteration: u32,
    pub timestamp: DateTime<Utc>,
    pub input: String,
    pub output: String,
    pub evaluation: Option<EvaluationResult>,
    pub feedback: String,
    pub improved: bool,
}

/// Evolver gene information
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GeneInfo {
    pub gene_id: String,
    pub version: String,
    pub category: String,
    pub signals: Vec<String>,
    pub preconditions: Vec<String>,
    pub strategy: Vec<String>,
    pub success_rate: f64,
    pub usage_count: u32,
}

/// Evolver capsule (execution unit) information
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CapsuleInfo {
    pub capsule_id: String,
    pub name: String,
    pub description: String,
    pub trigger: Vec<String>,
    pub gene_ref: String,
    pub gene_version: String,
    pub summary: String,
    pub created_at: DateTime<Utc>,
}

/// Evolver evolution event record
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EvolutionEventInfo {
    pub event_id: String,
    pub event_type: String,
    pub description: String,
    pub timestamp: DateTime<Utc>,
    pub metadata: HashMap<String, String>,
}

/// Evolver execution record
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EvolverExecution {
    pub engine_id: String,
    pub status: String,
    pub genes: Vec<GeneInfo>,
    pub capsules: Vec<CapsuleInfo>,
    pub events: Vec<EvolutionEventInfo>,
    pub selected_gene: Option<String>,
}

/// Security detection results
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SecurityResults {
    pub prompt_injection: Option<PromptInjectionRecord>,
    pub secrets_found: Vec<SecretRecord>,
    pub dangerous_code: Vec<DangerousCodeRecord>,
    pub firewall: Option<FirewallRecord>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PromptInjectionRecord {
    pub is_malicious: bool,
    pub severity: String,
    pub matched_patterns: Vec<String>,
    pub confidence: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SecretRecord {
    pub r#type: String,
    pub start: i32,
    pub end: i32,
    pub redacted: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DangerousCodeRecord {
    pub name: String,
    pub level: String,
    pub message: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FirewallRecord {
    pub allowed: bool,
    pub action: String,
    pub reason: String,
}

/// Complete execution context
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ExecutionContext {
    // Request identification
    pub request_id: String,
    pub timestamp: DateTime<Utc>,

    // Agent context (injected from Python)
    pub agent_id: String,
    pub agent_name: String,
    pub agent_repo_url: String,

    // Configuration injection
    pub skills: Vec<SkillInfo>,
    pub mcps: Vec<McpInfo>,
    pub hooks: Vec<HookInfo>,

    // Execution environment
    pub environment_vars: HashMap<String, String>,
    pub network_status: Option<NetworkStatus>,

    // Execution trajectory
    pub subagent_executions: Vec<SubAgentExecution>,
    pub evaluation_results: Vec<EvaluationResult>,
    pub iteration_history: Vec<IterationRecord>,

    // Evolver evolution records
    pub evolver_executions: Vec<EvolverExecution>,

    // Security results
    pub security_results: Option<SecurityResults>,

    // Resource usage
    pub memory_used_bytes: u64,
    pub cpu_time_ms: u64,
    pub execution_time_ms: u64,
}

impl ExecutionContext {
    pub fn new(request_id: String, agent_id: String, agent_name: String) -> Self {
        Self {
            request_id,
            timestamp: Utc::now(),
            agent_id,
            agent_name,
            agent_repo_url: String::new(),
            skills: Vec::new(),
            mcps: Vec::new(),
            hooks: Vec::new(),
            environment_vars: HashMap::new(),
            network_status: None,
            evolver_executions: Vec::new(),
            subagent_executions: Vec::new(),
            evaluation_results: Vec::new(),
            iteration_history: Vec::new(),
            security_results: None,
            memory_used_bytes: 0,
            cpu_time_ms: 0,
            execution_time_ms: 0,
        }
    }
}

/// Audit logger for full observability
pub struct AuditLogger {
    log_dir: PathBuf,
    current_date: String,
}

impl AuditLogger {
    pub fn new(log_dir: &str) -> Self {
        let log_path = PathBuf::from(log_dir);
        std::fs::create_dir_all(&log_path).ok();

        Self {
            log_dir: log_path,
            current_date: Utc::now().format("%Y-%m-%d").to_string(),
        }
    }

    fn get_log_file(&self) -> PathBuf {
        self.log_dir.join(format!("observability_{}.jsonl", self.current_date))
    }

    pub fn log(&self, context: &ExecutionContext) -> std::io::Result<()> {
        let log_file = self.get_log_file();

        let mut file = OpenOptions::new()
            .create(true)
            .append(true)
            .open(&log_file)?;

        let json = serde_json::to_string(context)?;
        writeln!(file, "{}", json)?;

        Ok(())
    }
}

/// Thread-safe audit logger
pub struct SharedAuditLogger {
    inner: Mutex<AuditLogger>,
}

impl SharedAuditLogger {
    pub fn new(log_dir: &str) -> Self {
        Self {
            inner: Mutex::new(AuditLogger::new(log_dir)),
        }
    }

    pub fn log(&self, context: &ExecutionContext) -> std::io::Result<()> {
        let logger = self.inner.lock().unwrap();
        logger.log(context)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_execution_context_creation() {
        let ctx = ExecutionContext::new(
            "test-123".to_string(),
            "agenticSeek".to_string(),
            "Jarvis".to_string(),
        );

        assert_eq!(ctx.request_id, "test-123");
        assert_eq!(ctx.agent_id, "agenticSeek");
        assert!(ctx.skills.is_empty());
    }

    #[test]
    fn test_audit_logger() {
        let logger = AuditLogger::new("/tmp/test-audit");
        let ctx = ExecutionContext::new(
            "test-456".to_string(),
            "test-agent".to_string(),
            "Test".to_string(),
        );

        logger.log(&ctx).ok();

        // Verify file was created
        let log_file = logger.get_log_file();
        assert!(log_file.exists());
    }
}

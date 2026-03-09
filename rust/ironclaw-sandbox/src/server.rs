//! IronClaw Sandbox Security Service
//!
//! A high-performance gRPC service for security detection

use std::net::SocketAddr;
use tonic::{transport::Server, Request, Response, Status};
use regex::Regex;
use lazy_static::lazy_static;
use tracing::{info, error};

// Import generated proto types
pub mod security {
    tonic::include_proto!("ironclaw");
}

use security::{
    security_service_server::SecurityService,
    PromptInjectionRequest, PromptInjectionResponse,
    SecretScanRequest, SecretScanResponse, SecretMatch,
    DangerousCodeRequest, DangerousCodeResponse, DangerousPattern,
    FirewallRequest, FirewallResponse,
    BatchCheckRequest, BatchCheckResponse,
};

lazy_static! {
    // Prompt injection patterns
    static ref IGNORE_INSTRUCTIONS: Vec<Regex> = vec![
        Regex::new(r"(?i)ignore\s+(all\s+)?(previous|prior|earlier)\s+instructions?").unwrap(),
        Regex::new(r"(?i)disregard\s+(all\s+)?(previous|prior|earlier)").unwrap(),
        Regex::new(r"(?i)forget\s+(everything|all)\s+you\s+(know|were\s+told)").unwrap(),
    ];

    static ref ROLE_OVERRIDE: Vec<Regex> = vec![
        Regex::new(r"(?i)you\s+are\s+(now|no\s+longer)\s+[a-z]+").unwrap(),
        Regex::new(r"(?i)act\s+as\s+(if|a|the)\s+[a-z]+").unwrap(),
        Regex::new(r"(?i)pretend\s+(to\s+be|you\s+are)").unwrap(),
    ];

    static ref JAILBREAK: Vec<Regex> = vec![
        Regex::new(r"(?i)\bDAN\b").unwrap(),
        Regex::new(r"(?i)developer\s+mode").unwrap(),
        Regex::new(r"(?i)jailbreak").unwrap(),
    ];

    // Secret patterns
    static ref OPENAI_KEY: Regex = Regex::new(r"sk-[a-zA-Z0-9]{20,}").unwrap();
    static ref GITHUB_TOKEN: Regex = Regex::new(r"gh[pousr]_[A-Za-z0-9_]{36,}").unwrap();
    static ref AWS_SECRET: Regex = Regex::new(r"(?i)aws[_-]?secret").unwrap();

    // Dangerous code patterns
    static ref EVAL_PATTERN: Regex = Regex::new(r"\beval\s*\(").unwrap();
    static ref EXEC_PATTERN: Regex = Regex::new(r"\bexec\s*\(").unwrap();
    static ref FILE_DELETE: Regex = Regex::new(r"os\.remove\s*\(|os\.unlink\s*\(").unwrap();
    static ref SUBPROCESS: Regex = Regex::new(r"subprocess\.(call|run|Popen)").unwrap();
}

#[derive(Default)]
pub struct SecurityServiceImpl {}

#[tonic::async_trait]
impl SecurityService for SecurityServiceImpl {
    async fn detect_prompt_injection(
        &self,
        request: Request<PromptInjectionRequest>,
    ) -> Result<Response<PromptInjectionResponse>, Status> {
        let req = request.into_inner();
        let content = req.content;

        let mut matched_patterns = Vec::new();
        let mut severity = "safe".to_string();

        // Check ignore instructions
        for pattern in IGNORE_INSTRUCTIONS.iter() {
            if pattern.is_match(&content) {
                matched_patterns.push("ignore_instructions".to_string());
                severity = "block".to_string();
                break;
            }
        }

        // Check role override
        for pattern in ROLE_OVERRIDE.iter() {
            if pattern.is_match(&content) {
                matched_patterns.push("role_override".to_string());
                severity = "block".to_string();
                break;
            }
        }

        // Check jailbreak
        for pattern in JAILBREAK.iter() {
            if pattern.is_match(&content) {
                matched_patterns.push("jailbreak".to_string());
                severity = "block".to_string();
                break;
            }
        }

        let confidence = if matched_patterns.is_empty() {
            0.0
        } else {
            0.85
        };

        let is_malicious = !matched_patterns.is_empty() && confidence >= req.threshold;

        Ok(Response::new(PromptInjectionResponse {
            is_malicious,
            severity,
            matched_patterns,
            confidence,
            sanitized_content: String::new(),
        }))
    }

    async fn scan_secrets(
        &self,
        request: Request<SecretScanRequest>,
    ) -> Result<Response<SecretScanResponse>, Status> {
        let req = request.into_inner();
        let content = req.content;

        let mut secrets_found = Vec::new();

        // Check OpenAI key
        if let Some(m) = OPENAI_KEY.find(&content) {
            secrets_found.push(SecretMatch {
                r#type: "openai_api_key".to_string(),
                start: m.start() as i32,
                end: m.end() as i32,
                snippet: m.as_str()[..10.min(m.as_str().len())].to_string(),
            });
        }

        // Check GitHub token
        if let Some(m) = GITHUB_TOKEN.find(&content) {
            secrets_found.push(SecretMatch {
                r#type: "github_token".to_string(),
                start: m.start() as i32,
                end: m.end() as i32,
                snippet: m.as_str()[..10.min(m.as_str().len())].to_string(),
            });
        }

        // Check AWS secret
        if AWS_SECRET.is_match(&content) {
            secrets_found.push(SecretMatch {
                r#type: "aws_secret_key".to_string(),
                start: 0,
                end: 10,
                snippet: "AWS_SECRET".to_string(),
            });
        }

        let has_secrets = !secrets_found.is_empty();

        // Redact if requested
        let redacted_content = if req.redact && has_secrets {
            "[REDACTED]".to_string()
        } else {
            String::new()
        };

        Ok(Response::new(SecretScanResponse {
            has_secrets,
            secrets_found,
            redacted_content,
        }))
    }

    async fn detect_dangerous_code(
        &self,
        request: Request<DangerousCodeRequest>,
    ) -> Result<Response<DangerousCodeResponse>, Status> {
        let req = request.into_inner();
        let code = req.code;

        let mut detected = Vec::new();
        let mut level = "safe".to_string();

        // Check eval
        if EVAL_PATTERN.is_match(&code) {
            detected.push(DangerousPattern {
                name: "eval_usage".to_string(),
                level: "critical".to_string(),
                message: "eval() allows arbitrary code execution".to_string(),
            });
            level = "critical".to_string();
        }

        // Check exec
        if EXEC_PATTERN.is_match(&code) && level != "critical" {
            detected.push(DangerousPattern {
                name: "exec_usage".to_string(),
                level: "critical".to_string(),
                message: "exec() allows arbitrary code execution".to_string(),
            });
            level = "critical".to_string();
        }

        // Check file delete
        if FILE_DELETE.is_match(&code) && level != "critical" {
            detected.push(DangerousPattern {
                name: "os_remove".to_string(),
                level: "high".to_string(),
                message: "File deletion detected".to_string(),
            });
            if level == "safe" {
                level = "high".to_string();
            }
        }

        // Check subprocess
        if SUBPROCESS.is_match(&code) && level == "safe" {
            detected.push(DangerousPattern {
                name: "subprocess_call".to_string(),
                level: "medium".to_string(),
                message: "Subprocess execution detected".to_string(),
            });
            level = "medium".to_string();
        }

        let is_safe = detected.is_empty();
        let warnings: Vec<String> = detected.iter().map(|p| p.message.clone()).collect();

        Ok(Response::new(DangerousCodeResponse {
            is_safe,
            level,
            warnings,
            detected_patterns: detected,
        }))
    }

    async fn check_firewall(
        &self,
        request: Request<FirewallRequest>,
    ) -> Result<Response<FirewallResponse>, Status> {
        let req = request.into_inner();

        // Block internal IPs
        let ip = req.ip;
        if !ip.is_empty() && (ip.starts_with("127.") || ip.starts_with("10.") || ip.starts_with("192.168.")) {
            return Ok(Response::new(FirewallResponse {
                allowed: false,
                action: "block".to_string(),
                reason: "Internal IP blocked".to_string(),
            }));
        }

        // Block localhost
        let domain = req.domain;
        if !domain.is_empty() && (domain == "localhost" || domain == "127.0.0.1") {
            return Ok(Response::new(FirewallResponse {
                allowed: false,
                action: "block".to_string(),
                reason: "Localhost blocked".to_string(),
            }));
        }

        Ok(Response::new(FirewallResponse {
            allowed: true,
            action: "allow".to_string(),
            reason: "Allowed".to_string(),
        }))
    }

    async fn batch_check(
        &self,
        request: Request<BatchCheckRequest>,
    ) -> Result<Response<BatchCheckResponse>, Status> {
        let req = request.into_inner();

        let mut prompt_responses = Vec::new();
        let mut secret_responses = Vec::new();
        let mut code_responses = Vec::new();

        // Process prompt requests
        for pr in req.prompt_requests {
            let result = self.detect_prompt_injection(
                Request::new(pr)
            ).await?;
            prompt_responses.push(result.into_inner());
        }

        // Process secret requests
        for sr in req.secret_requests {
            let result = self.scan_secrets(
                Request::new(sr)
            ).await?;
            secret_responses.push(result.into_inner());
        }

        // Process code requests
        for cr in req.code_requests {
            let result = self.detect_dangerous_code(
                Request::new(cr)
            ).await?;
            code_responses.push(result.into_inner());
        }

        Ok(Response::new(BatchCheckResponse {
            prompt_responses,
            secret_responses,
            code_responses,
        }))
    }
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Initialize logging
    tracing_subscriber::fmt::init();

    let addr = SocketAddr::from(([0, 0, 0, 0], 50051));

    info!("Starting IronClaw Security Service on {}", addr);

    let service = SecurityServiceImpl::default();

    Server::builder()
        .add_service(security::security_service_server::SecurityServiceServer::new(service))
        .serve(addr)
        .await?;

    Ok(())
}

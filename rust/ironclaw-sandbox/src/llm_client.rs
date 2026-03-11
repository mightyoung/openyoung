//! LLM Client - 调用外部 LLM API
//!
//! 基于 Jeff Dean 的大规模系统设计原则：连接池、重试机制

use reqwest::Client;
use serde::{Deserialize, Serialize};
use serde_json::json;
use std::time::Duration;
use tokio::sync::RwLock;
use tracing::{error, info};

#[derive(Debug, thiserror::Error)]
pub enum LLMError {
    #[error("HTTP request failed: {0}")]
    RequestError(#[from] reqwest::Error),
    #[error("API error: {0}")]
    ApiError(String),
    #[error("Parse error: {0}")]
    ParseError(String),
    #[error("Timeout")]
    Timeout,
}

#[derive(Debug, Clone)]
pub struct LLMConfig {
    pub api_key: String,
    pub endpoint: String,
    pub model: String,
    pub timeout_secs: u64,
}

impl Default for LLMConfig {
    fn default() -> Self {
        Self {
            api_key: std::env::var("OPENAI_API_KEY").unwrap_or_default(),
            endpoint: std::env::var("LLM_ENDPOINT")
                .unwrap_or_else(|_| "https://api.openai.com/v1/chat/completions".to_string()),
            model: std::env::var("LLM_MODEL")
                .unwrap_or_else(|_| "claude-sonnet-4-20250514".to_string()),
            timeout_secs: 60,
        }
    }
}

#[derive(Debug, Serialize)]
struct ChatRequest {
    model: String,
    messages: Vec<Message>,
    max_tokens: Option<u32>,
    temperature: Option<f32>,
}

#[derive(Debug, Serialize, Deserialize)]
struct Message {
    role: String,
    content: String,
}

#[derive(Debug, Deserialize)]
struct ChatResponse {
    choices: Vec<Choice>,
    #[serde(default)]
    usage: Option<Usage>,
}

#[derive(Debug, Deserialize)]
struct Choice {
    message: ResponseMessage,
}

#[derive(Debug, Deserialize)]
struct ResponseMessage {
    content: String,
}

#[derive(Debug, Deserialize, Default)]
struct Usage {
    #[serde(default)]
    prompt_tokens: Option<u32>,
    #[serde(default)]
    completion_tokens: Option<u32>,
    #[serde(default)]
    total_tokens: Option<u32>,
}

pub struct LLMClient {
    config: LLMConfig,
    client: Client,
    // 连接池状态
    stats: RwLock<LLMStats>,
}

#[derive(Debug, Default, Clone)]
pub struct LLMStats {
    pub total_requests: u64,
    pub successful_requests: u64,
    pub failed_requests: u64,
    pub total_tokens: u64,
}

impl LLMClient {
    pub fn new(config: LLMConfig) -> Self {
        let client = Client::builder()
            .timeout(Duration::from_secs(config.timeout_secs))
            .pool_max_idle_per_host(10)
            .build()
            .expect("Failed to build HTTP client");

        Self {
            config,
            client,
            stats: RwLock::new(LLMStats::default()),
        }
    }

    pub async fn chat(&self, prompt: String) -> Result<String, LLMError> {
        let request = ChatRequest {
            model: self.config.model.clone(),
            messages: vec![Message {
                role: "user".to_string(),
                content: prompt,
            }],
            max_tokens: Some(4096),
            temperature: Some(0.7),
        };

        info!("Sending request to LLM: model={}", self.config.model);

        let response = self.client
            .post(&self.config.endpoint)
            .header("Authorization", format!("Bearer {}", self.config.api_key))
            .header("Content-Type", "application/json")
            .json(&request)
            .send()
            .await?;

        if !response.status().is_success() {
            let status = response.status();
            let error_text = response.text().await.unwrap_or_default();
            error!("LLM API error: {} - {}", status, error_text);

            {
                let mut stats = self.stats.write().await;
                stats.failed_requests += 1;
            }

            return Err(LLMError::ApiError(format!("{} - {}", status, error_text)));
        }

        let chat_response: ChatResponse = response.json().await?;

        let content = chat_response
            .choices
            .first()
            .map(|c| c.message.content.clone())
            .ok_or_else(|| LLMError::ParseError("No choices in response".to_string()))?;

        // 更新统计
        {
            let mut stats = self.stats.write().await;
            stats.total_requests += 1;
            stats.successful_requests += 1;
            if let Some(usage) = chat_response.usage {
                stats.total_tokens += usage.total_tokens.unwrap_or(0) as u64;
            }
        }

        info!("LLM request successful, content length: {}", content.len());
        Ok(content)
    }

    pub async fn chat_with_messages(&self, messages: Vec<(String, String)>) -> Result<String, LLMError> {
        let request = ChatRequest {
            model: self.config.model.clone(),
            messages: messages
                .into_iter()
                .map(|(role, content)| Message { role, content })
                .collect(),
            max_tokens: Some(4096),
            temperature: Some(0.7),
        };

        let response = self.client
            .post(&self.config.endpoint)
            .header("Authorization", format!("Bearer {}", self.config.api_key))
            .header("Content-Type", "application/json")
            .json(&request)
            .send()
            .await?;

        if !response.status().is_success() {
            let status = response.status();
            let error_text = response.text().await.unwrap_or_default();
            error!("LLM API error: {} - {}", status, error_text);

            {
                let mut stats = self.stats.write().await;
                stats.failed_requests += 1;
            }

            return Err(LLMError::ApiError(format!("{} - {}", status, error_text)));
        }

        let chat_response: ChatResponse = response.json().await?;

        let content = chat_response
            .choices
            .first()
            .map(|c| c.message.content.clone())
            .ok_or_else(|| LLMError::ParseError("No choices in response".to_string()))?;

        // 更新统计
        {
            let mut stats = self.stats.write().await;
            stats.total_requests += 1;
            stats.successful_requests += 1;
            if let Some(usage) = chat_response.usage {
                stats.total_tokens += usage.total_tokens.unwrap_or(0) as u64;
            }
        }

        Ok(content)
    }

    pub async fn get_stats(&self) -> LLMStats {
        self.stats.read().await.clone()
    }
}

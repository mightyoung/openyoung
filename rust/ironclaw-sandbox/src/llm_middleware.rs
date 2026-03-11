//! LLM Middleware - LLM 中间层
//!
//! 统一管理 Target Agent 和 Evaluator 的 LLM 调用
//! 集成熔断器、连接池、统计等功能

use crate::circuit_breaker::{CircuitBreaker, CircuitBreakerConfig, CircuitState};
use crate::llm_client::{LLMClient, LLMConfig, LLMError, LLMStats};
use std::sync::Arc;
use tokio::sync::RwLock;
use tracing::{error, info, warn};

/// LLM 调用者类型
#[derive(Debug, Clone, PartialEq)]
pub enum LLMCaller {
    /// Target Agent - 执行任务
    TargetAgent,
    /// Evaluator - 评估结果
    Evaluator,
}

impl std::fmt::Display for LLMCaller {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            LLMCaller::TargetAgent => write!(f, "TargetAgent"),
            LLMCaller::Evaluator => write!(f, "Evaluator"),
        }
    }
}

/// 模型配置
#[derive(Debug, Clone)]
pub struct ModelConfig {
    /// 模型名称
    pub name: String,
    /// API 端点
    pub endpoint: String,
    /// API 密钥
    pub api_key: String,
    /// 最大连接数
    pub max_connections: u32,
    /// 超时时间(秒)
    pub timeout_secs: u64,
    /// 默认温度
    pub temperature: f32,
    /// 最大 token 数
    pub max_tokens: u32,
}

impl Default for ModelConfig {
    fn default() -> Self {
        // 支持多 Provider 配置
        // 优先级: LLM_MODEL > DEEPSEEK_MODEL > CLAUDE_MODEL
        let (name, endpoint, api_key) = if let Ok(model) = std::env::var("LLM_MODEL") {
            // 完全自定义配置
            let endpoint = std::env::var("LLM_ENDPOINT")
                .unwrap_or_else(|_| "https://api.openai.com/v1/chat/completions".to_string());
            let api_key = std::env::var("OPENAI_API_KEY").unwrap_or_default();
            (model, endpoint, api_key)
        } else if let Ok(key) = std::env::var("DEEPSEEK_API_KEY") {
            // DeepSeek provider
            ("deepseek-chat".to_string(), "https://api.deepseek.com/v1/chat/completions".to_string(), key)
        } else if let Ok(key) = std::env::var("ANTHROPIC_API_KEY") {
            // Anthropic/Claude provider
            ("claude-3-sonnet-20240229".to_string(), "https://api.anthropic.com/v1/messages".to_string(), key)
        } else if let Ok(key) = std::env::var("MOONSHOT_API_KEY") {
            // Moonshot provider
            ("moonshot-v1-8k".to_string(), "https://api.moonshot.cn/v1/chat/completions".to_string(), key)
        } else if let Ok(key) = std::env::var("DASHSCOPE_API_KEY") {
            // DashScope (Qwen) provider
            ("qwen-turbo".to_string(), "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions".to_string(), key)
        } else if let Ok(key) = std::env::var("GEMINI_API_KEY") {
            // Google Gemini provider
            ("gemini-2.0-flash".to_string(), "https://generativelanguage.googleapis.com/v1beta/models".to_string(), key)
        } else {
            // Fallback to OpenAI defaults
            (
                "claude-sonnet-4-20250514".to_string(),
                "https://api.openai.com/v1/chat/completions".to_string(),
                std::env::var("OPENAI_API_KEY").unwrap_or_default(),
            )
        };

        Self {
            name,
            endpoint,
            api_key,
            max_connections: 10,
            timeout_secs: 60,
            temperature: 0.7,
            max_tokens: 4096,
        }
    }
}

impl From<ModelConfig> for LLMConfig {
    fn from(cfg: ModelConfig) -> Self {
        Self {
            api_key: cfg.api_key,
            endpoint: cfg.endpoint,
            model: cfg.name,
            timeout_secs: cfg.timeout_secs,
        }
    }
}

/// LLM 中间层配置
#[derive(Debug, Clone)]
pub struct LLMMiddlewareConfig {
    /// Target Agent 模型配置
    pub target_model: ModelConfig,
    /// Evaluator 模型配置
    pub evaluator_model: ModelConfig,
    /// 熔断器配置
    pub circuit_breaker: CircuitBreakerConfig,
}

impl Default for LLMMiddlewareConfig {
    fn default() -> Self {
        Self {
            target_model: ModelConfig::default(),
            evaluator_model: ModelConfig::default(),
            circuit_breaker: CircuitBreakerConfig::default(),
        }
    }
}

/// LLM 中间层
///
/// 统一管理所有 LLM 调用，提供：
/// - 熔断器保护
/// - 统计信息
/// - 连接池管理
pub struct LLMMiddleware {
    target_client: LLMClient,
    evaluator_client: LLMClient,
    target_circuit: Arc<CircuitBreaker>,
    evaluator_circuit: Arc<CircuitBreaker>,
    config: LLMMiddlewareConfig,
    stats: Arc<RwLock<MiddlewareStats>>,
}

/// 中间层统计信息
#[derive(Debug, Default, Clone)]
pub struct MiddlewareStats {
    /// 按调用者分类的请求数
    pub target_requests: u64,
    pub evaluator_requests: u64,
    /// 按调用者分类的成功数
    pub target_successes: u64,
    pub evaluator_successes: u64,
    /// 按调用者分类的失败数
    pub target_failures: u64,
    pub evaluator_failures: u64,
    /// 熔断器触发次数
    pub circuit_breaks: u64,
}

impl LLMMiddleware {
    /// 创建新的 LLM 中间层
    pub fn new(config: LLMMiddlewareConfig) -> Self {
        let target_client = LLMClient::new(config.target_model.clone().into());
        let evaluator_client = LLMClient::new(config.evaluator_model.clone().into());
        let target_circuit = Arc::new(CircuitBreaker::new(config.circuit_breaker.clone()));
        let evaluator_circuit = Arc::new(CircuitBreaker::new(config.circuit_breaker.clone()));

        Self {
            target_client,
            evaluator_client,
            target_circuit,
            evaluator_circuit,
            config,
            stats: Arc::new(RwLock::new(MiddlewareStats::default())),
        }
    }

    /// 调用 LLM
    ///
    /// # Arguments
    /// * `caller` - 调用者类型 (TargetAgent 或 Evaluator)
    /// * `prompt` - 提示词
    ///
    /// # Returns
    /// LLM 响应内容
    pub async fn call(&self, caller: LLMCaller, prompt: String) -> Result<String, LLMError> {
        // 选择对应的客户端和熔断器
        let (client, circuit, caller_str) = match caller {
            LLMCaller::TargetAgent => (&self.target_client, &self.target_circuit, "TargetAgent"),
            LLMCaller::Evaluator => (&self.evaluator_client, &self.evaluator_circuit, "Evaluator"),
        };

        // 检查熔断器
        if !circuit.can_execute().await {
            warn!("Circuit breaker is open for {}", caller_str);

            {
                let mut stats = self.stats.write().await;
                stats.circuit_breaks += 1;
            }

            return Err(LLMError::ApiError("Circuit breaker is open".to_string()));
        }

        // 执行请求
        match client.chat(prompt).await {
            Ok(response) => {
                // 记录成功
                circuit.record_success().await;

                let mut stats = self.stats.write().await;
                match caller {
                    LLMCaller::TargetAgent => {
                        stats.target_requests += 1;
                        stats.target_successes += 1;
                    }
                    LLMCaller::Evaluator => {
                        stats.evaluator_requests += 1;
                        stats.evaluator_successes += 1;
                    }
                }

                info!("LLM call succeeded for {}", caller_str);
                Ok(response)
            }
            Err(e) => {
                // 记录失败
                circuit.record_failure().await;

                let mut stats = self.stats.write().await;
                match caller {
                    LLMCaller::TargetAgent => {
                        stats.target_requests += 1;
                        stats.target_failures += 1;
                    }
                    LLMCaller::Evaluator => {
                        stats.evaluator_requests += 1;
                        stats.evaluator_failures += 1;
                    }
                }

                error!("LLM call failed for {}: {}", caller_str, e);
                Err(e)
            }
        }
    }

    /// 调用 LLM (带消息历史)
    pub async fn call_with_messages(
        &self,
        caller: LLMCaller,
        messages: Vec<(String, String)>,
    ) -> Result<String, LLMError> {
        let (client, circuit, caller_str) = match caller {
            LLMCaller::TargetAgent => (&self.target_client, &self.target_circuit, "TargetAgent"),
            LLMCaller::Evaluator => (&self.evaluator_client, &self.evaluator_circuit, "Evaluator"),
        };

        if !circuit.can_execute().await {
            warn!("Circuit breaker is open for {}", caller_str);
            return Err(LLMError::ApiError("Circuit breaker is open".to_string()));
        }

        match client.chat_with_messages(messages).await {
            Ok(response) => {
                circuit.record_success().await;
                info!("LLM call with messages succeeded for {}", caller_str);
                Ok(response)
            }
            Err(e) => {
                circuit.record_failure().await;
                error!("LLM call with messages failed for {}: {}", caller_str, e);
                Err(e)
            }
        }
    }

    /// 获取统计信息
    pub async fn get_stats(&self) -> MiddlewareStats {
        self.stats.read().await.clone()
    }

    /// 获取熔断器状态
    pub async fn get_circuit_state(&self, caller: LLMCaller) -> CircuitState {
        match caller {
            LLMCaller::TargetAgent => self.target_circuit.get_state().await,
            LLMCaller::Evaluator => self.evaluator_circuit.get_state().await,
        }
    }

    /// 重置熔断器
    pub async fn reset_circuit(&self, caller: LLMCaller) {
        match caller {
            LLMCaller::TargetAgent => self.target_circuit.reset().await,
            LLMCaller::Evaluator => self.evaluator_circuit.reset().await,
        }
        info!("Circuit breaker reset for {:?}", caller);
    }
}

impl Default for LLMMiddleware {
    fn default() -> Self {
        Self::new(LLMMiddlewareConfig::default())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_middleware_stats() {
        let middleware = LLMMiddleware::default();
        let stats = middleware.get_stats().await;

        assert_eq!(stats.target_requests, 0);
        assert_eq!(stats.evaluator_requests, 0);
    }

    #[tokio::test]
    async fn test_circuit_state() {
        let middleware = LLMMiddleware::default();

        let state = middleware.get_circuit_state(LLMCaller::TargetAgent).await;
        assert_eq!(state, CircuitState::Closed);
    }
}

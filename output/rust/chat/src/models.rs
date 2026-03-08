use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize)]
pub struct ChatMessage {
    pub role: String,
    pub content: String,
}

impl ChatMessage {
    pub fn new(role: &str, content: &str) -> Self {
        Self {
            role: role.to_string(),
            content: content.to_string(),
        }
    }
    
    pub fn user(content: &str) -> Self {
        Self::new("user", content)
    }
    
    pub fn assistant(content: &str) -> Self {
        Self::new("assistant", content)
    }
    
    pub fn system(content: &str) -> Self {
        Self::new("system", content)
    }
}

#[derive(Debug, Clone, Serialize)]
pub struct ChatRequest {
    pub model: String,
    pub messages: Vec<ChatMessage>,
    pub temperature: f32,
    pub max_tokens: Option<u32>,
}

#[derive(Debug, Clone, Deserialize)]
pub struct ChatResponse {
    pub choices: Vec<Choice>,
    pub usage: Option<Usage>,
}

#[derive(Debug, Clone, Deserialize)]
pub struct Choice {
    pub message: ChatMessage,
    pub finish_reason: Option<String>,
}

#[derive(Debug, Clone, Deserialize)]
pub struct Usage {
    pub prompt_tokens: u32,
    pub completion_tokens: u32,
    pub total_tokens: u32,
}

#[derive(Debug, Clone, Serialize)]
pub struct AnthropicRequest {
    pub model: String,
    pub messages: Vec<AnthropicMessage>,
    pub max_tokens: u32,
    pub temperature: f32,
}

#[derive(Debug, Clone, Serialize)]
pub struct AnthropicMessage {
    pub role: String,
    pub content: String,
}

#[derive(Debug, Clone, Deserialize)]
pub struct AnthropicResponse {
    pub content: Vec<AnthropicContent>,
    pub usage: AnthropicUsage,
}

#[derive(Debug, Clone, Deserialize)]
pub struct AnthropicContent {
    pub text: String,
    #[serde(rename = "type")]
    pub content_type: String,
}

#[derive(Debug, Clone, Deserialize)]
pub struct AnthropicUsage {
    pub input_tokens: u32,
    pub output_tokens: u32,
}

#[derive(Debug, Clone)]
pub enum Provider {
    OpenAI,
    Anthropic,
    Ollama,
    Local,
}

impl Provider {
    pub fn from_str(s: &str) -> Self {
        match s.to_lowercase().as_str() {
            "openai" => Self::OpenAI,
            "anthropic" => Self::Anthropic,
            "claude" => Self::Anthropic,
            "ollama" => Self::Ollama,
            "local" => Self::Local,
            _ => Self::OpenAI,
        }
    }
    
    pub fn default_model(&self) -> &'static str {
        match self {
            Self::OpenAI => "gpt-3.5-turbo",
            Self::Anthropic => "claude-3-haiku-20240307",
            Self::Ollama => "llama2",
            Self::Local => "local-model",
        }
    }
}
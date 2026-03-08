//! Error types for the chat bot

use thiserror::Error;

/// Main error type for the chat bot
#[derive(Error, Debug)]
pub enum BotError {
    /// Configuration error
    #[error("Configuration error: {0}")]
    Config(String),
    
    /// Storage error
    #[error("Storage error: {0}")]
    Storage(String),
    
    /// Conversation error
    #[error("Conversation error: {0}")]
    Conversation(String),
    
    /// Response generation error
    #[error("Response generation error: {0}")]
    Response(String),
    
    /// IO error
    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),
    
    /// JSON serialization/deserialization error
    #[error("JSON error: {0}")]
    Json(#[from] serde_json::Error),
    
    /// Other errors
    #[error("Other error: {0}")]
    Other(String),
}

/// Result type alias for the chat bot
pub type BotResult<T> = Result<T, BotError>;
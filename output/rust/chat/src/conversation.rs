//! Conversation management

use serde::{Deserialize, Serialize};
use uuid::Uuid;
use chrono::{DateTime, Utc};
use std::collections::VecDeque;

/// Message role in conversation
#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq)]
pub enum Role {
    /// User message
    User,
    /// Bot message
    Bot,
    /// System message
    System,
}

/// A single message in a conversation
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Message {
    /// Unique message ID
    pub id: Uuid,
    /// Message content
    pub content: String,
    /// Message role
    pub role: Role,
    /// Timestamp
    pub timestamp: DateTime<Utc>,
}

impl Message {
    /// Create a new message
    pub fn new(content: impl Into<String>, role: Role) -> Self {
        Self {
            id: Uuid::new_v4(),
            content: content.into(),
            role,
            timestamp: Utc::now(),
        }
    }
    
    /// Create a user message
    pub fn user(content: impl Into<String>) -> Self {
        Self::new(content, Role::User)
    }
    
    /// Create a bot message
    pub fn bot(content: impl Into<String>) -> Self {
        Self::new(content, Role::Bot)
    }
    
    /// Create a system message
    pub fn system(content: impl Into<String>) -> Self {
        Self::new(content, Role::System)
    }
}

/// A conversation between user and bot
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Conversation {
    /// Unique conversation ID
    pub id: Uuid,
    /// Conversation messages
    pub messages: VecDeque<Message>,
    /// Maximum number of messages to keep
    pub max_length: usize,
    /// Conversation start time
    pub started_at: DateTime<Utc>,
    /// Last activity time
    pub last_activity: DateTime<Utc>,
}

impl Conversation {
    /// Create a new conversation
    pub fn new(max_length: usize) -> Self {
        let now = Utc::now();
        Self {
            id: Uuid::new_v4(),
            messages: VecDeque::with_capacity(max_length),
            max_length,
            started_at: now,
            last_activity: now,
        }
    }
    
    /// Add a message to the conversation
    pub fn add_message(&mut self, message: Message) {
        // Remove oldest message if we're at capacity
        if self.messages.len() >= self.max_length {
            self.messages.pop_front();
        }
        
        self.messages.push_back(message);
        self.last_activity = Utc::now();
    }
    
    /// Add a user message
    pub fn add_user_message(&mut self, content: impl Into<String>) {
        self.add_message(Message::user(content));
    }
    
    /// Add a bot message
    pub fn add_bot_message(&mut self, content: impl Into<String>) {
        self.add_message(Message::bot(content));
    }
    
    /// Get all messages as a vector
    pub fn messages(&self) -> Vec<&Message> {
        self.messages.iter().collect()
    }
    
    /// Get the last message
    pub fn last_message(&self) -> Option<&Message> {
        self.messages.back()
    }
    
    /// Get user messages
    pub fn user_messages(&self) -> Vec<&Message> {
        self.messages
            .iter()
            .filter(|m| m.role == Role::User)
            .collect()
    }
    
    /// Get bot messages
    pub fn bot_messages(&self) -> Vec<&Message> {
        self.messages
            .iter()
            .filter(|m| m.role == Role::Bot)
            .collect()
    }
    
    /// Clear all messages
    pub fn clear(&mut self) {
        self.messages.clear();
    }
    
    /// Check if conversation is empty
    pub fn is_empty(&self) -> bool {
        self.messages.is_empty()
    }
    
    /// Get conversation length
    pub fn len(&self) -> usize {
        self.messages.len()
    }
    
    /// Get conversation duration
    pub fn duration(&self) -> chrono::Duration {
        Utc::now() - self.started_at
    }
}
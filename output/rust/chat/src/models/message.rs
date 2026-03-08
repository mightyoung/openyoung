//! Message model definitions

use serde::{Deserialize, Serialize};
use uuid::Uuid;
use chrono::{DateTime, Utc};

/// Message type
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum MessageType {
    Text,
    File,
    Image,
    System,
}

/// Message status
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum MessageStatus {
    Sent,
    Delivered,
    Read,
    Failed,
}

/// Chat message
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Message {
    /// Unique message ID
    pub id: Uuid,
    /// Sender user ID
    pub sender_id: Uuid,
    /// Receiver user ID (or session ID for group chats)
    pub receiver_id: Uuid,
    /// Message content
    pub content: String,
    /// Message type
    pub message_type: MessageType,
    /// Message status
    pub status: MessageStatus,
    /// Timestamp when message was created
    pub created_at: DateTime<Utc>,
    /// Timestamp when message was last updated
    pub updated_at: DateTime<Utc>,
}

impl Message {
    /// Create a new text message
    pub fn new_text(sender_id: Uuid, receiver_id: Uuid, content: String) -> Self {
        let now = Utc::now();
        Self {
            id: Uuid::new_v4(),
            sender_id,
            receiver_id,
            content,
            message_type: MessageType::Text,
            status: MessageStatus::Sent,
            created_at: now,
            updated_at: now,
        }
    }

    /// Create a new system message
    pub fn new_system(receiver_id: Uuid, content: String) -> Self {
        let now = Utc::now();
        Self {
            id: Uuid::new_v4(),
            sender_id: Uuid::nil(), // System messages have nil sender
            receiver_id,
            content,
            message_type: MessageType::System,
            status: MessageStatus::Sent,
            created_at: now,
            updated_at: now,
        }
    }

    /// Mark message as delivered
    pub fn mark_delivered(&mut self) {
        self.status = MessageStatus::Delivered;
        self.updated_at = Utc::now();
    }

    /// Mark message as read
    pub fn mark_read(&mut self) {
        self.status = MessageStatus::Read;
        self.updated_at = Utc::now();
    }

    /// Check if message is from system
    pub fn is_system_message(&self) -> bool {
        self.sender_id.is_nil()
    }
}

/// Message filter for querying
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MessageFilter {
    pub sender_id: Option<Uuid>,
    pub receiver_id: Option<Uuid>,
    pub message_type: Option<MessageType>,
    pub status: Option<MessageStatus>,
    pub start_time: Option<DateTime<Utc>>,
    pub end_time: Option<DateTime<Utc>>,
    pub limit: Option<usize>,
    pub offset: Option<usize>,
}

impl Default for MessageFilter {
    fn default() -> Self {
        Self {
            sender_id: None,
            receiver_id: None,
            message_type: None,
            status: None,
            start_time: None,
            end_time: None,
            limit: Some(50),
            offset: Some(0),
        }
    }
}
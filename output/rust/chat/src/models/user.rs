//! User model definitions

use serde::{Deserialize, Serialize};
use uuid::Uuid;
use chrono::{DateTime, Utc};

/// User role
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum UserRole {
    User,
    Admin,
    Bot,
}

/// User status
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum UserStatus {
    Active,
    Inactive,
    Banned,
}

/// Chat user
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct User {
    /// Unique user ID
    pub id: Uuid,
    /// Username
    pub username: String,
    /// Display name
    pub display_name: String,
    /// User role
    pub role: UserRole,
    /// User status
    pub status: UserStatus,
    /// Timestamp when user was created
    pub created_at: DateTime<Utc>,
    /// Timestamp when user was last updated
    pub updated_at: DateTime<Utc>,
}

impl User {
    /// Create a new user
    pub fn new(username: String, display_name: String, role: UserRole) -> Self {
        let now = Utc::now();
        Self {
            id: Uuid::new_v4(),
            username,
            display_name,
            role,
            status: UserStatus::Active,
            created_at: now,
            updated_at: now,
        }
    }

    /// Create a new bot user
    pub fn new_bot(username: String, display_name: String) -> Self {
        Self::new(username, display_name, UserRole::Bot)
    }

    /// Check if user is a bot
    pub fn is_bot(&self) -> bool {
        matches!(self.role, UserRole::Bot)
    }

    /// Check if user is active
    pub fn is_active(&self) -> bool {
        matches!(self.status, UserStatus::Active)
    }

    /// Deactivate user
    pub fn deactivate(&mut self) {
        self.status = UserStatus::Inactive;
        self.updated_at = Utc::now();
    }

    /// Activate user
    pub fn activate(&mut self) {
        self.status = UserStatus::Active;
        self.updated_at = Utc::now();
    }
}

/// User filter for querying
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UserFilter {
    pub username: Option<String>,
    pub role: Option<UserRole>,
    pub status: Option<UserStatus>,
    pub limit: Option<usize>,
    pub offset: Option<usize>,
}

impl Default for UserFilter {
    fn default() -> Self {
        Self {
            username: None,
            role: None,
            status: None,
            limit: Some(50),
            offset: Some(0),
        }
    }
}
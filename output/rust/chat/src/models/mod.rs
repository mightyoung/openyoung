//! Data models for the chat bot

pub mod message;
pub mod user;
pub mod conversation;

pub use message::Message;
pub use user::User;
pub use conversation::Conversation;
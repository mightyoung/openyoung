//! Chat Bot Library
//! 
//! A modular chat bot system built in Rust with support for:
//! - Multiple response strategies
//! - Conversation history
//! - Configurable behavior
//! - Extensible architecture

pub mod bot;
pub mod config;
pub mod conversation;
pub mod responses;
pub mod errors;
pub mod storage;

pub use bot::ChatBot;
pub use config::BotConfig;
pub use conversation::{Conversation, Message, Role};
pub use errors::BotError;
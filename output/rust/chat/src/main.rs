use anyhow::Result;
use clap::{Parser, Subcommand};
use colored::*;
use std::env;

mod bot;
mod config;
mod handlers;
mod models;
mod utils;

use crate::bot::ChatBot;
use crate::config::Config;

#[derive(Parser)]
#[command(name = "rust-chatbot")]
#[command(about = "A Rust-based chatbot with multiple AI providers support")]
#[command(version = "0.1.0")]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    /// Start the chatbot in interactive mode
    Start {
        /// Provider to use (openai, anthropic, ollama, local)
        #[arg(short, long, default_value = "openai")]
        provider: String,
        
        /// Model to use
        #[arg(short, long)]
        model: Option<String>,
        
        /// API key (if not set in .env)
        #[arg(short, long)]
        api_key: Option<String>,
    },
    
    /// Chat with a single message
    Chat {
        /// Message to send
        message: String,
        
        /// Provider to use
        #[arg(short, long, default_value = "openai")]
        provider: String,
        
        /// Model to use
        #[arg(short, long)]
        model: Option<String>,
    },
    
    /// Configure the chatbot
    Config {
        /// Set API key
        #[arg(short, long)]
        api_key: Option<String>,
        
        /// Set default provider
        #[arg(short, long)]
        provider: Option<String>,
        
        /// Set default model
        #[arg(short, long)]
        model: Option<String>,
    },
}

#[tokio::main]
async fn main() -> Result<()> {
    // Load environment variables
    dotenv::dotenv().ok();
    
    let cli = Cli::parse();
    
    match cli.command {
        Commands::Start { provider, model, api_key } => {
            let config = Config::load()?;
            let mut chatbot = ChatBot::new(config, provider, model, api_key).await?;
            chatbot.run_interactive().await?;
        }
        Commands::Chat { message, provider, model } => {
            let config = Config::load()?;
            let mut chatbot = ChatBot::new(config, provider, model, None).await?;
            let response = chatbot.send_message(&message).await?;
            println!("{}", response);
        }
        Commands::Config { api_key, provider, model } => {
            let mut config = Config::load()?;
            
            if let Some(key) = api_key {
                config.set_api_key(&key);
                println!("{}", "API key updated".green());
            }
            
            if let Some(prov) = provider {
                config.set_default_provider(&prov);
                println!("{}: {}", "Default provider set".green(), prov);
            }
            
            if let Some(modl) = model {
                config.set_default_model(&modl);
                println!("{}: {}", "Default model set".green(), modl);
            }
            
            config.save()?;
            println!("{}", "Configuration saved".green());
        }
    }
    
    Ok(())
}
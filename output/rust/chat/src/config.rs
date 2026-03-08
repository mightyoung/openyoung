use anyhow::Result;
use serde::{Deserialize, Serialize};
use std::fs;
use std::path::Path;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Config {
    pub openai_api_key: Option<String>,
    pub anthropic_api_key: Option<String>,
    pub default_provider: String,
    pub default_model: String,
    pub temperature: f32,
    pub max_tokens: Option<u32>,
}

impl Default for Config {
    fn default() -> Self {
        Self {
            openai_api_key: None,
            anthropic_api_key: None,
            default_provider: "openai".to_string(),
            default_model: "gpt-3.5-turbo".to_string(),
            temperature: 0.7,
            max_tokens: Some(1000),
        }
    }
}

impl Config {
    pub fn load() -> Result<Self> {
        let config_path = Self::config_path();
        
        if config_path.exists() {
            let content = fs::read_to_string(&config_path)?;
            let config = serde_json::from_str(&content)?;
            Ok(config)
        } else {
            let config = Self::default();
            config.save()?;
            Ok(config)
        }
    }
    
    pub fn save(&self) -> Result<()> {
        let config_path = Self::config_path();
        let config_dir = config_path.parent().unwrap();
        
        if !config_dir.exists() {
            fs::create_dir_all(config_dir)?;
        }
        
        let content = serde_json::to_string_pretty(self)?;
        fs::write(&config_path, content)?;
        Ok(())
    }
    
    fn config_path() -> std::path::PathBuf {
        let home = std::env::var("HOME").unwrap_or_else(|_| ".".to_string());
        Path::new(&home).join(".config").join("rust-chatbot").join("config.json")
    }
    
    pub fn set_api_key(&mut self, key: &str) {
        match self.default_provider.as_str() {
            "openai" => self.openai_api_key = Some(key.to_string()),
            "anthropic" => self.anthropic_api_key = Some(key.to_string()),
            _ => {}
        }
    }
    
    pub fn set_default_provider(&mut self, provider: &str) {
        self.default_provider = provider.to_string();
    }
    
    pub fn set_default_model(&mut self, model: &str) {
        self.default_model = model.to_string();
    }
    
    pub fn get_api_key(&self, provider: &str) -> Option<&String> {
        match provider {
            "openai" => self.openai_api_key.as_ref(),
            "anthropic" => self.anthropic_api_key.as_ref(),
            _ => None,
        }
    }
}
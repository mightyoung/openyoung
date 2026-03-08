use std::io::{self, Write};
use chrono::Local;
use rand::seq::SliceRandom;
use rand::thread_rng;

struct ChatBot {
    name: String,
    responses: Vec<(&'static str, &'static str)>,
    jokes: Vec<&'static str>,
    conversation_history: Vec<(String, String)>,
}

impl ChatBot {
    fn new(name: &str) -> Self {
        ChatBot {
            name: name.to_string(),
            responses: vec![
                ("hello", "Hello! How can I help you today?"),
                ("hi", "Hi there! Nice to meet you!"),
                ("how are you", "I'm doing great, thanks for asking!"),
                ("what is your name", "My name is Rusty, I'm a Rust chatbot!"),
                ("bye", "Goodbye! Have a great day!"),
                ("help", "I can respond to: hello, hi, how are you, what is your name, bye, help, time, date, joke, history, clear"),
                ("weather", "I'm not sure about the weather, but I hope it's nice where you are!"),
                ("time", "I can tell you the current time!"),
                ("date", "I can tell you today's date!"),
                ("joke", "I know some programming jokes!"),
                ("thank you", "You're welcome! Happy to help!"),
                ("history", "I can show you our conversation history!"),
                ("clear", "I can clear the conversation history!"),
            ],
            jokes: vec![
                "Why do Rust programmers prefer dark mode? Because light attracts bugs!",
                "What's a Rustacean's favorite music? Heavy metal!",
                "Why did the Rust developer break up with JavaScript? Because it kept promising things it couldn't deliver!",
                "How many Rust programmers does it take to change a light bulb? None, that's a compile-time error!",
                "Why was the Rust struct feeling lonely? Because it had no traits!",
            ],
            conversation_history: Vec::new(),
        }
    }

    fn respond(&mut self, input: &str) -> String {
        let input_lower = input.to_lowercase().trim().to_string();
        
        // Special commands
        if input_lower == "time" {
            let now = Local::now();
            return format!("Current time is: {}", now.format("%H:%M:%S"));
        }
        
        if input_lower == "date" {
            let now = Local::now();
            return format!("Today's date is: {}", now.format("%Y-%m-%d"));
        }
        
        if input_lower == "joke" {
            let mut rng = thread_rng();
            if let Some(joke) = self.jokes.choose(&mut rng) {
                return joke.to_string();
            }
            return "I'm out of jokes!".to_string();
        }
        
        if input_lower == "history" {
            if self.conversation_history.is_empty() {
                return "No conversation history yet.".to_string();
            }
            let mut history = String::from("Conversation History:\n");
            for (i, (user, bot)) in self.conversation_history.iter().enumerate() {
                history.push_str(&format!("{}. You: {}\n   Bot: {}\n", i + 1, user, bot));
            }
            return history;
        }
        
        if input_lower == "clear" {
            self.conversation_history.clear();
            return "Conversation history cleared!".to_string();
        }
        
        // Regular keyword matching
        for (keyword, response) in &self.responses {
            if input_lower.contains(keyword) {
                return response.to_string();
            }
        }
        
        // Default response if no keyword matches
        format!("I'm not sure how to respond to '{}'. Try saying hello, asking for help, or telling a joke!", input)
    }

    fn get_name(&self) -> &str {
        &self.name
    }
    
    fn add_to_history(&mut self, user_input: &str, bot_response: &str) {
        self.conversation_history.push((user_input.to_string(), bot_response.to_string()));
    }
}

fn print_welcome() {
    println!("╔══════════════════════════════════════════════════════╗");
    println!("║                🤖 RUST CHATBOT v1.0                 ║");
    println!("╠══════════════════════════════════════════════════════╣");
    println!("║ Commands:                                           ║");
    println!("║   • hello/hi - Greet the bot                        ║");
    println!("║   • time - Get current time                         ║");
    println!("║   • date - Get today's date                         ║");
    println!("║   • joke - Hear a programming joke                  ║");
    println!("║   • history - View conversation history             ║");
    println!("║   • clear - Clear history                           ║");
    println!("║   • help - Show available commands                  ║");
    println!("║   • exit/quit - End conversation                    ║");
    println!("╚══════════════════════════════════════════════════════╝");
    println!();
}

fn main() {
    print_welcome();
    
    let mut bot = ChatBot::new("Rusty");
    println!("Bot: Hello! I'm {}. How can I assist you today?", bot.get_name());
    
    let mut message_count = 0;
    
    loop {
        print!("You: ");
        io::stdout().flush().unwrap();
        
        let mut input = String::new();
        io::stdin().read_line(&mut input).expect("Failed to read line");
        
        let input = input.trim();
        
        if input.is_empty() {
            continue;
        }
        
        if input.eq_ignore_ascii_case("exit") || input.eq_ignore_ascii_case("quit") {
            println!("Bot: Goodbye! Thanks for chatting!");
            println!("Total messages exchanged: {}", message_count);
            break;
        }
        
        let response = bot.respond(input);
        println!("Bot: {}", response);
        
        // Add to history
        bot.add_to_history(input, &response);
        message_count += 1;
        
        println!("{}", "─".repeat(50));
    }
}
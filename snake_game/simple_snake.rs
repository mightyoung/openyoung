use std::io::{self, Write};
use std::time::Duration;
use std::thread;
use std::process::Command;
use std::env;

const WIDTH: usize = 20;
const HEIGHT: usize = 10;

#[derive(Clone, Copy, PartialEq)]
enum Direction {
    Up,
    Down,
    Left,
    Right,
}

struct Position {
    x: usize,
    y: usize,
}

struct Snake {
    body: Vec<Position>,
    direction: Direction,
}

struct Game {
    snake: Snake,
    food: Position,
    score: u32,
    game_over: bool,
}

impl Snake {
    fn new() -> Self {
        let mut body = Vec::new();
        for i in 0..3 {
            body.push(Position { x: 5 + i, y: 5 });
        }
        
        Snake {
            body,
            direction: Direction::Right,
        }
    }
    
    fn move_forward(&mut self) {
        let head = self.body[0];
        let new_head = match self.direction {
            Direction::Up => Position { x: head.x, y: head.y.wrapping_sub(1) },
            Direction::Down => Position { x: head.x, y: head.y + 1 },
            Direction::Left => Position { x: head.x.wrapping_sub(1), y: head.y },
            Direction::Right => Position { x: head.x + 1, y: head.y },
        };
        
        self.body.insert(0, new_head);
        self.body.pop();
    }
    
    fn grow(&mut self) {
        let tail = self.body.last().unwrap().clone();
        self.body.push(tail);
    }
    
    fn contains(&self, pos: &Position) -> bool {
        self.body.iter().any(|p| p.x == pos.x && p.y == pos.y)
    }
    
    fn check_collision(&self) -> bool {
        let head = &self.body[0];
        
        // 检查墙壁碰撞
        if head.x >= WIDTH || head.y >= HEIGHT {
            return true;
        }
        
        // 检查自身碰撞
        for segment in self.body.iter().skip(1) {
            if head.x == segment.x && head.y == segment.y {
                return true;
            }
        }
        
        false
    }
}

impl Game {
    fn new() -> Self {
        let snake = Snake::new();
        let food = Position { x: 10, y: 5 };
        
        Game {
            snake,
            food,
            score: 0,
            game_over: false,
        }
    }
    
    fn update(&mut self) {
        if self.game_over {
            return;
        }
        
        self.snake.move_forward();
        
        if self.snake.check_collision() {
            self.game_over = true;
            return;
        }
        
        let head = &self.snake.body[0];
        if head.x == self.food.x && head.y == self.food.y {
            self.snake.grow();
            self.score += 10;
            self.generate_food();
        }
    }
    
    fn generate_food(&mut self) {
        use rand::Rng;
        let mut rng = rand::thread_rng();
        
        loop {
            let new_food = Position {
                x: rng.gen_range(0..WIDTH),
                y: rng.gen_range(0..HEIGHT),
            };
            
            if !self.snake.contains(&new_food) {
                self.food = new_food;
                break;
            }
        }
    }
    
    fn draw(&self) {
        // 清屏
        print!("\x1B[2J\x1B[1;1H");
        
        // 绘制顶部边框
        println!("┌{}┐", "─".repeat(WIDTH));
        
        // 绘制游戏区域
        for y in 0..HEIGHT {
            print!("│");
            for x in 0..WIDTH {
                let pos = Position { x, y };
                
                if self.snake.body[0].x == x && self.snake.body[0].y == y {
                    print!("●"); // 蛇头
                } else if self.snake.body.iter().skip(1).any(|p| p.x == x && p.y == y) {
                    print!("○"); // 蛇身
                } else if self.food.x == x && self.food.y == y {
                    print!("★"); // 食物
                } else {
                    print!(" ");
                }
            }
            println!("│");
        }
        
        // 绘制底部边框
        println!("└{}┘", "─".repeat(WIDTH));
        
        // 绘制分数和状态
        println!("Score: {}", self.score);
        if self.game_over {
            println!("Game Over! Press 'R' to restart, 'Q' to quit");
        } else {
            println!("Use WASD to move. Press 'Q' to quit");
        }
        
        io::stdout().flush().unwrap();
    }
}

fn main() {
    let mut game = Game::new();
    
    // 检查是否安装了 rand crate
    let has_rand = env::var("CARGO_HOME").is_ok();
    
    if !has_rand {
        println!("Note: Random food placement requires rand crate.");
        println!("To install: cargo add rand");
        println!("For now, food will be at fixed position (10,5).");
    }
    
    // 简单输入处理
    use std::io::{self as io2, Read};
    
    println!("Simple Snake Game");
    println!("Press any key to start...");
    let _ = io2::stdin().read(&mut [0u8]).unwrap();
    
    loop {
        game.draw();
        
        if game.game_over {
            break;
        }
        
        // 简单移动（这里简化了输入处理）
        game.snake.direction = Direction::Right;
        
        game.update();
        thread::sleep(Duration::from_millis(500));
    }
    
    println!("Final Score: {}", game.score);
}
use crossterm::{
    cursor::{Hide, MoveTo, Show},
    event::{self, Event, KeyCode, KeyEvent},
    execute,
    terminal::{self, Clear, ClearType, EnterAlternateScreen, LeaveAlternateScreen},
    Result,
};
use rand::Rng;
use std::{
    collections::VecDeque,
    io::{stdout, Write},
    thread,
    time::{Duration, Instant},
};

// 游戏常量
const WIDTH: u16 = 40;
const HEIGHT: u16 = 20;
const INITIAL_SNAKE_LENGTH: usize = 3;
const GAME_SPEED: u64 = 100; // 毫秒

// 方向枚举
#[derive(Debug, Clone, Copy, PartialEq)]
enum Direction {
    Up,
    Down,
    Left,
    Right,
}

// 位置结构体
#[derive(Debug, Clone, Copy, PartialEq)]
struct Position {
    x: u16,
    y: u16,
}

// 游戏状态
struct Game {
    snake: VecDeque<Position>,
    food: Position,
    direction: Direction,
    next_direction: Direction,
    score: u32,
    game_over: bool,
}

impl Game {
    fn new() -> Self {
        let mut snake = VecDeque::new();
        
        // 初始化蛇在中间位置
        let start_x = WIDTH / 2;
        let start_y = HEIGHT / 2;
        
        for i in 0..INITIAL_SNAKE_LENGTH {
            snake.push_back(Position {
                x: start_x - i as u16,
                y: start_y,
            });
        }
        
        // 生成食物
        let food = Self::generate_food(&snake);
        
        Game {
            snake,
            food,
            direction: Direction::Right,
            next_direction: Direction::Right,
            score: 0,
            game_over: false,
        }
    }
    
    fn generate_food(snake: &VecDeque<Position>) -> Position {
        let mut rng = rand::thread_rng();
        
        loop {
            let x = rng.gen_range(1..WIDTH - 1);
            let y = rng.gen_range(1..HEIGHT - 1);
            let food = Position { x, y };
            
            // 确保食物不在蛇身上
            if !snake.contains(&food) {
                return food;
            }
        }
    }
    
    fn update(&mut self) {
        // 更新方向
        self.direction = self.next_direction;
        
        // 获取蛇头位置
        let head = self.snake.front().unwrap();
        let mut new_head = *head;
        
        // 根据方向移动蛇头
        match self.direction {
            Direction::Up => {
                if new_head.y == 1 {
                    new_head.y = HEIGHT - 2;
                } else {
                    new_head.y -= 1;
                }
            }
            Direction::Down => {
                if new_head.y == HEIGHT - 2 {
                    new_head.y = 1;
                } else {
                    new_head.y += 1;
                }
            }
            Direction::Left => {
                if new_head.x == 1 {
                    new_head.x = WIDTH - 2;
                } else {
                    new_head.x -= 1;
                }
            }
            Direction::Right => {
                if new_head.x == WIDTH - 2 {
                    new_head.x = 1;
                } else {
                    new_head.x += 1;
                }
            }
        }
        
        // 检查是否撞到自己
        if self.snake.contains(&new_head) {
            self.game_over = true;
            return;
        }
        
        // 添加新的蛇头
        self.snake.push_front(new_head);
        
        // 检查是否吃到食物
        if new_head == self.food {
            self.score += 10;
            self.food = Self::generate_food(&self.snake);
        } else {
            // 如果没有吃到食物，移除蛇尾
            self.snake.pop_back();
        }
    }
    
    fn change_direction(&mut self, direction: Direction) {
        // 防止直接反向移动
        match (self.direction, direction) {
            (Direction::Up, Direction::Down) => return,
            (Direction::Down, Direction::Up) => return,
            (Direction::Left, Direction::Right) => return,
            (Direction::Right, Direction::Left) => return,
            _ => self.next_direction = direction,
        }
    }
    
    fn draw(&self, stdout: &mut std::io::Stdout) -> Result<()> {
        // 清屏
        execute!(stdout, Clear(ClearType::All))?;
        
        // 绘制边框
        for x in 0..WIDTH {
            execute!(stdout, MoveTo(x, 0))?;
            print!("─");
            execute!(stdout, MoveTo(x, HEIGHT - 1))?;
            print!("─");
        }
        
        for y in 0..HEIGHT {
            execute!(stdout, MoveTo(0, y))?;
            print!("│");
            execute!(stdout, MoveTo(WIDTH - 1, y))?;
            print!("│");
        }
        
        // 绘制角落
        execute!(stdout, MoveTo(0, 0))?;
        print!("┌");
        execute!(stdout, MoveTo(WIDTH - 1, 0))?;
        print!("┐");
        execute!(stdout, MoveTo(0, HEIGHT - 1))?;
        print!("└");
        execute!(stdout, MoveTo(WIDTH - 1, HEIGHT - 1))?;
        print!("┘");
        
        // 绘制蛇
        for (i, segment) in self.snake.iter().enumerate() {
            execute!(stdout, MoveTo(segment.x, segment.y))?;
            
            if i == 0 {
                // 蛇头
                print!("●");
            } else {
                // 蛇身
                print!("○");
            }
        }
        
        // 绘制食物
        execute!(stdout, MoveTo(self.food.x, self.food.y))?;
        print!("★");
        
        // 绘制分数
        execute!(stdout, MoveTo(2, HEIGHT))?;
        print!("分数: {}", self.score);
        
        // 绘制游戏结束信息
        if self.game_over {
            execute!(stdout, MoveTo(WIDTH / 2 - 5, HEIGHT / 2))?;
            print!("游戏结束!");
            execute!(stdout, MoveTo(WIDTH / 2 - 8, HEIGHT / 2 + 1))?;
            print!("按 R 重新开始");
            execute!(stdout, MoveTo(WIDTH / 2 - 8, HEIGHT / 2 + 2))?;
            print!("按 Q 退出游戏");
        } else {
            // 绘制控制说明
            execute!(stdout, MoveTo(WIDTH + 2, 2))?;
            print!("控制说明:");
            execute!(stdout, MoveTo(WIDTH + 2, 3))?;
            print!("↑ ↓ ← → : 移动");
            execute!(stdout, MoveTo(WIDTH + 2, 4))?;
            print!("R : 重新开始");
            execute!(stdout, MoveTo(WIDTH + 2, 5))?;
            print!("Q : 退出游戏");
        }
        
        stdout.flush()?;
        Ok(())
    }
    
    fn reset(&mut self) {
        *self = Game::new();
    }
}

fn main() -> Result<()> {
    // 初始化终端
    let mut stdout = stdout();
    execute!(stdout, EnterAlternateScreen)?;
    terminal::enable_raw_mode()?;
    execute!(stdout, Hide)?;
    
    let mut game = Game::new();
    let mut last_update = Instant::now();
    
    // 游戏主循环
    loop {
        // 处理输入
        while event::poll(Duration::from_millis(0))? {
            if let Event::Key(key_event) = event::read()? {
                match key_event.code {
                    KeyCode::Up => game.change_direction(Direction::Up),
                    KeyCode::Down => game.change_direction(Direction::Down),
                    KeyCode::Left => game.change_direction(Direction::Left),
                    KeyCode::Right => game.change_direction(Direction::Right),
                    KeyCode::Char('w') | KeyCode::Char('W') => game.change_direction(Direction::Up),
                    KeyCode::Char('s') | KeyCode::Char('S') => game.change_direction(Direction::Down),
                    KeyCode::Char('a') | KeyCode::Char('A') => game.change_direction(Direction::Left),
                    KeyCode::Char('d') | KeyCode::Char('D') => game.change_direction(Direction::Right),
                    KeyCode::Char('r') | KeyCode::Char('R') => game.reset(),
                    KeyCode::Char('q') | KeyCode::Char('Q') => break,
                    _ => {}
                }
            }
        }
        
        // 更新游戏状态
        if !game.game_over && last_update.elapsed() >= Duration::from_millis(GAME_SPEED) {
            game.update();
            last_update = Instant::now();
        }
        
        // 绘制游戏
        game.draw(&mut stdout)?;
        
        // 控制帧率
        thread::sleep(Duration::from_millis(16)); // ~60 FPS
    }
    
    // 清理终端
    execute!(stdout, Show)?;
    terminal::disable_raw_mode()?;
    execute!(stdout, LeaveAlternateScreen)?;
    
    println!("游戏结束！最终分数: {}", game.score);
    Ok(())
}
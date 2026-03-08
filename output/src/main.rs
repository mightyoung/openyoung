use crossterm::{
    event::{self, Event, KeyCode, KeyEvent},
    execute,
    terminal::{Clear, ClearType, EnterAlternateScreen, LeaveAlternateScreen},
};
use rand::Rng;
use std::collections::VecDeque;
use std::io::Write;
use std::thread;
use std::time::Duration;

// 游戏常量
const WIDTH: usize = 40;
const HEIGHT: usize = 20;
const INITIAL_SNAKE_LENGTH: usize = 3;
const GAME_SPEED_MS: u64 = 100;

// 方向
#[derive(Clone, Copy, PartialEq)]
enum Direction {
    Up,
    Down,
    Left,
    Right,
}

#[derive(Clone, Copy, PartialEq)]
struct Position {
    x: usize,
    y: usize,
}

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
        // 初始化蛇的位置
        let start_x = WIDTH / 2;
        let start_y = HEIGHT / 2;
        for i in 0..INITIAL_SNAKE_LENGTH {
            snake.push_back(Position {
                x: start_x + i,
                y: start_y,
            });
        }

        let food = Game::spawn_food(&snake);

        Game {
            snake,
            food,
            direction: Direction::Right,
            next_direction: Direction::Right,
            score: 0,
            game_over: false,
        }
    }

    fn spawn_food(snake: &VecDeque<Position>) -> Position {
        let mut rng = rand::thread_rng();
        loop {
            let food = Position {
                x: rng.gen_range(1..WIDTH - 1),
                y: rng.gen_range(1..HEIGHT - 1),
            };
            if !snake.contains(&food) {
                return food;
            }
        }
    }

    fn update(&mut self) {
        // 更新方向
        self.direction = self.next_direction;

        // 计算新头部位置
        let head = self.snake.front().unwrap();
        let mut new_head = *head;

        match self.direction {
            Direction::Up => {
                if new_head.y > 1 {
                    new_head.y -= 1;
                } else {
                    self.game_over = true;
                    return;
                }
            }
            Direction::Down => {
                if new_head.y < HEIGHT - 2 {
                    new_head.y += 1;
                } else {
                    self.game_over = true;
                    return;
                }
            }
            Direction::Left => {
                if new_head.x > 1 {
                    new_head.x -= 1;
                } else {
                    self.game_over = true;
                    return;
                }
            }
            Direction::Right => {
                if new_head.x < WIDTH - 2 {
                    new_head.x += 1;
                } else {
                    self.game_over = true;
                    return;
                }
            }
        }

        // 检查是否撞到自己
        for segment in self.snake.iter().skip(1) {
            if segment.x == new_head.x && segment.y == new_head.y {
                self.game_over = true;
                return;
            }
        }

        // 添加新头部
        self.snake.push_front(new_head);

        // 检查是否吃到食物
        if new_head.x == self.food.x && new_head.y == self.food.y {
            self.score += 10;
            self.food = Game::spawn_food(&self.snake);
        } else {
            self.snake.pop_back();
        }
    }

    fn change_direction(&mut self, new_direction: Direction) {
        // 防止直接反向移动
        match (&self.direction, &new_direction) {
            (Direction::Up, Direction::Down) => return,
            (Direction::Down, Direction::Up) => return,
            (Direction::Left, Direction::Right) => return,
            (Direction::Right, Direction::Left) => return,
            _ => {}
        }
        self.next_direction = new_direction;
    }

    fn render(&self) -> String {
        let mut buffer = String::new();
        buffer.push_str("\n");
        buffer.push_str(&"  ".repeat(WIDTH / 2));
        buffer.push_str("🐍 RUST SNAKE GAME 🐍\n\n");

        // 绘制上边框
        buffer.push_str("  ");
        for _ in 0..WIDTH {
            buffer.push_str("▀");
        }
        buffer.push('\n');

        // 绘制游戏区域
        for y in 1..HEIGHT - 1 {
            buffer.push_str("  █");
            for x in 1..WIDTH - 1 {
                let pos = Position { x, y };
                if x == self.food.x && y == self.food.y {
                    buffer.push_str("🍎");
                } else if self.snake.contains(&pos) {
                    let index = self.snake.iter().position(|p| p.x == x && p.y == y).unwrap();
                    if index == 0 {
                        buffer.push_str("🟢");
                    } else {
                        buffer.push_str("🟩");
                    }
                } else {
                    buffer.push_str("  ");
                }
            }
            buffer.push_str("█\n");
        }

        // 绘制下边框
        buffer.push_str("  ");
        for _ in 0..WIDTH {
            buffer.push_str("▄");
        }
        buffer.push_str("\n\n");
        buffer.push_str(&format!("  Score: {}  |  Use arrow keys to move  |  Press 'q' to quit\n", self.score));

        if self.game_over {
            buffer.push_str("\n  ╔══════════════════════════════╗\n");
            buffer.push_str("  ║      GAME OVER!             ║\n");
            buffer.push_str(&format!("  ║    Final Score: {}          ║\n", self.score));
            buffer.push_str("  ║    Press 'r' to restart     ║\n");
            buffer.push_str("  ╚══════════════════════════════╝\n");
        }

        buffer
    }
}

fn main() {
    // 设置终端
    let mut stdout = std::io::stdout();
    let _ = execute!(stdout, EnterAlternateScreen, Clear(ClearType::All));
    let _ = crossterm::terminal::enable_raw_mode();

    let mut game = Game::new();

    // 游戏主循环
    loop {
        // 渲染游戏
        let render = game.render();
        print!("{}", render);
        stdout.flush().unwrap();

        if game.game_over {
            // 等待用户输入
            if let Ok(Event::Key(KeyEvent { code, .. })) = event::read() {
                match code {
                    KeyCode::Char('q') | KeyCode::Esc => break,
                    KeyCode::Char('r') => {
                        game = Game::new();
                    }
                    _ => {}
                }
            }
            continue;
        }

        // 处理输入
        if let Ok(Event::Key(KeyEvent { code, .. })) = event::read() {
            match code {
                KeyCode::Up => game.change_direction(Direction::Up),
                KeyCode::Down => game.change_direction(Direction::Down),
                KeyCode::Left => game.change_direction(Direction::Left),
                KeyCode::Right => game.change_direction(Direction::Right),
                KeyCode::Char('q') | KeyCode::Esc => break,
                _ => {}
            }
        }

        // 更新游戏状态
        game.update();

        // 控制游戏速度
        thread::sleep(Duration::from_millis(GAME_SPEED_MS));
    }

    // 恢复终端
    let _ = crossterm::terminal::disable_raw_mode();
    let _ = execute!(stdout, LeaveAlternateScreen);
    println!("Thanks for playing!\n");
}

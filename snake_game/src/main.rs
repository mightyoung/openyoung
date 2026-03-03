use crossterm::{
    cursor::{Hide, MoveTo, Show},
    event::{self, Event, KeyCode, KeyEvent},
    execute,
    terminal::{self, Clear, ClearType, EnterAlternateScreen, LeaveAlternateScreen},
};
use std::io::{self, Write, Result};
use std::time::{Duration, Instant};
use rand::Rng;

const WIDTH: u16 = 40;
const HEIGHT: u16 = 20;
const INITIAL_SNAKE_LENGTH: usize = 3;

#[derive(Debug, Clone, Copy, PartialEq)]
enum Direction {
    Up,
    Down,
    Left,
    Right,
}

#[derive(Clone)]
struct Snake {
    body: Vec<(u16, u16)>,
    direction: Direction,
}

impl Snake {
    fn new() -> Self {
        let mut body = Vec::new();
        let start_x = WIDTH / 2;
        let start_y = HEIGHT / 2;
        for i in 0..INITIAL_SNAKE_LENGTH {
            body.push((start_x - i as u16, start_y));
        }
        Snake {
            body,
            direction: Direction::Right,
        }
    }

    fn head(&self) -> (u16, u16) {
        self.body[0]
    }

    fn move_snake(&mut self) {
        let head = self.head();
        let new_head = match self.direction {
            Direction::Up => (head.0, head.1.saturating_sub(1)),
            Direction::Down => (head.0, head.1 + 1),
            Direction::Left => (head.0.saturating_sub(1), head.1),
            Direction::Right => (head.0 + 1, head.1),
        };
        
        if new_head.0 == 0 || new_head.0 >= WIDTH - 1 || new_head.1 == 0 || new_head.1 >= HEIGHT - 1 {
            return;
        }
        
        if self.body[1..].contains(&new_head) {
            return;
        }
        
        self.body.insert(0, new_head);
        self.body.pop();
    }

    fn grow(&mut self) {
        let tail = self.body.last().unwrap();
        self.body.push(*tail);
    }

    fn change_direction(&mut self, new_direction: Direction) {
        match (self.direction, new_direction) {
            (Direction::Up, Direction::Down) |
            (Direction::Down, Direction::Up) |
            (Direction::Left, Direction::Right) |
            (Direction::Right, Direction::Left) => return,
            _ => self.direction = new_direction,
        }
    }
}

struct Game {
    snake: Snake,
    food: (u16, u16),
    score: i32,
    game_over: bool,
}

impl Game {
    fn new() -> Self {
        let mut rng = rand::thread_rng();
        let food = (
            rng.gen_range(1..WIDTH - 1),
            rng.gen_range(1..HEIGHT - 1),
        );
        Game {
            snake: Snake::new(),
            food,
            score: 0,
            game_over: false,
        }
    }

    fn update(&mut self) {
        if self.game_over {
            return;
        }

        let old_head = self.snake.head();
        self.snake.move_snake();
        let new_head = self.snake.head();

        if new_head == self.food {
            self.score += 10;
            self.snake.grow();
            let mut rng = rand::thread_rng();
            self.food = (
                rng.gen_range(1..WIDTH - 1),
                rng.gen_range(1..HEIGHT - 1),
            );
        }

        if new_head.0 == 0 || new_head.0 >= WIDTH - 1 || new_head.1 == 0 || new_head.1 >= HEIGHT - 1 {
            self.game_over = true;
        }

        if self.snake.body[1..].contains(&new_head) {
            self.game_over = true;
        }
    }

    fn draw(&self) -> Result<()> {
        use std::io::Write;
        
        let mut stdout = std::io::stdout();
        execute!(stdout, Clear(ClearType::All))?;
        
        for x in 0..WIDTH {
            execute!(stdout, MoveTo(x, 0))?;
            print!("─");
        }
        for x in 0..WIDTH {
            execute!(stdout, MoveTo(x, HEIGHT - 1))?;
            print!("─");
        }
        for y in 0..HEIGHT {
            execute!(stdout, MoveTo(0, y))?;
            print!("│");
            execute!(stdout, MoveTo(WIDTH - 1, y))?;
            print!("│");
        }
        
        execute!(stdout, MoveTo(0, 0))?;
        print!("┌");
        execute!(stdout, MoveTo(WIDTH - 1, 0))?;
        print!("┐");
        execute!(stdout, MoveTo(0, HEIGHT - 1))?;
        print!("└");
        execute!(stdout, MoveTo(WIDTH - 1, HEIGHT - 1))?;
        print!("┘");

        for (i, &(x, y)) in self.snake.body.iter().enumerate() {
            execute!(stdout, MoveTo(x, y))?;
            if i == 0 {
                print!("●");
            } else {
                print!("○");
            }
        }

        execute!(stdout, MoveTo(self.food.0, self.food.1))?;
        print!("★");

        execute!(stdout, MoveTo(0, HEIGHT))?;
        println!("分数: {}  方向键移动, ESC退出", self.score);

        if self.game_over {
            execute!(stdout, MoveTo(WIDTH / 2 - 5, HEIGHT / 2))?;
            print!("游戏结束!");
            execute!(stdout, MoveTo(WIDTH / 2 - 8, HEIGHT / 2 + 1))?;
            print!("最终分数: {}", self.score);
        }

        stdout.flush()?;
        Ok(())
    }
}

fn main() -> Result<()> {
    use std::io::{stdin, Write};
    
    terminal::enable_raw_mode()?;
    execute!(std::io::stdout(), EnterAlternateScreen, Hide)?;

    let mut game = Game::new();
    let mut last_update = Instant::now();
    let mut stdout = std::io::stdout();

    loop {
        if event::poll(Duration::from_millis(10))? {
            if let Event::Key(key_event) = event::read()? {
                match key_event.code {
                    KeyCode::Up => game.snake.change_direction(Direction::Up),
                    KeyCode::Down => game.snake.change_direction(Direction::Down),
                    KeyCode::Left => game.snake.change_direction(Direction::Left),
                    KeyCode::Right => game.snake.change_direction(Direction::Right),
                    KeyCode::Esc => break,
                    _ => {}
                }
            }
        }

        if last_update.elapsed() >= Duration::from_millis(150) {
            game.update();
            last_update = Instant::now();
        }

        game.draw()?;

        if game.game_over {
            loop {
                if event::poll(Duration::from_millis(100))? {
                    if let Event::Key(_) = event::read()? {
                        break;
                    }
                }
            }
            break;
        }

        std::thread::sleep(Duration::from_millis(10));
    }

    execute!(stdout, Show, LeaveAlternateScreen)?;
    terminal::disable_raw_mode()?;
    
    Ok(())
}

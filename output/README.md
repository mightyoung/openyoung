# Rust 贪吃蛇游戏

一个使用Rust和Piston图形库编写的经典贪吃蛇游戏。

## 功能特点

- 经典的贪吃蛇游戏玩法
- 分数系统
- 随着分数增加，游戏速度逐渐加快
- 游戏结束检测（撞墙或撞到自己）
- 重新开始功能
- 网格显示

## 控制方式

- **方向键上**: 向上移动
- **方向键下**: 向下移动  
- **方向键左**: 向左移动
- **方向键右**: 向右移动
- **R键**: 游戏结束后重新开始
- **ESC键**: 退出游戏

## 运行要求

- Rust 1.56.0 或更高版本
- Cargo (Rust包管理器)

## 安装和运行

### 1. 克隆或下载项目

```bash
cd output
```

### 2. 运行游戏

```bash
cargo run --release
```

### 3. 构建发布版本

```bash
cargo build --release
```

编译后的可执行文件将位于 `target/release/snake_game`

## 游戏规则

1. 控制蛇吃红色食物
2. 每吃到一个食物，蛇的长度增加，分数增加10分
3. 游戏速度会随着分数增加而逐渐加快
4. 游戏结束条件：
   - 蛇撞到墙壁
   - 蛇撞到自己的身体

## 项目结构

```
output/
├── Cargo.toml          # Rust项目配置文件
├── README.md           # 项目说明文档
└── src/
    └── main.rs         # 游戏主程序
```

## 依赖库

- `piston`: 游戏引擎框架
- `piston2d-graphics`: 2D图形渲染
- `pistoncore-glutin_window`: 窗口管理
- `piston2d-opengl_graphics`: OpenGL图形后端
- `rand`: 随机数生成

## 自定义设置

你可以在 `src/main.rs` 中修改以下常量来调整游戏：

```rust
const GRID_SIZE: i32 = 20;      // 网格大小（像素）
const GRID_WIDTH: i32 = 30;     // 网格宽度（格子数）
const GRID_HEIGHT: i32 = 20;    // 网格高度（格子数）
const INITIAL_SPEED: f64 = 10.0; // 初始速度（更新次数/秒）
```

## 故障排除

如果遇到编译问题：

1. 确保安装了正确的OpenGL版本
2. 更新Rust和Cargo到最新版本：
   ```bash
   rustup update
   ```
3. 清理并重新构建：
   ```bash
   cargo clean
   cargo build
   ```

## 许可证

MIT License
# Rust 贪吃蛇游戏

一个使用 Rust 和 crossterm 库编写的终端贪吃蛇游戏。

## 功能特点

- 经典的贪吃蛇游戏玩法
- 终端图形界面
- 分数系统
- 游戏结束检测
- 重新开始功能
- 边界穿越（从一边出去从另一边进来）

## 控制方式

- **方向键** 或 **WASD**: 控制蛇的移动方向
- **R**: 重新开始游戏
- **Q**: 退出游戏

## 运行要求

- Rust 1.70 或更高版本
- 支持 ANSI 转义序列的终端

## 安装和运行

### 1. 克隆或下载项目

```bash
cd output/snake_game
```

### 2. 运行游戏

```bash
cargo run --release
```

### 3. 构建可执行文件

```bash
cargo build --release
```

构建后的可执行文件位于 `target/release/snake_game`

## 游戏规则

1. 控制蛇吃掉食物（★）
2. 每吃到一个食物得10分
3. 蛇不能撞到自己
4. 蛇可以穿越边界（从一边出去从另一边进来）

## 项目结构

```
snake_game/
├── Cargo.toml      # 项目配置和依赖
├── src/
│   └── main.rs     # 主程序文件
└── README.md       # 说明文档
```

## 依赖库

- `crossterm`: 跨平台终端操作库
- `rand`: 随机数生成库

## 编译和测试

```bash
# 检查代码
cargo check

# 编译调试版本
cargo build

# 编译发布版本（优化）
cargo build --release

# 运行测试
cargo test
```

## 故障排除

如果遇到终端显示问题：
1. 确保终端支持 ANSI 转义序列
2. 尝试调整终端窗口大小
3. 在支持彩色显示的终端中运行

## 许可证

MIT License
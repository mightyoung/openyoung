#!/bin/bash

echo "正在构建贪吃蛇游戏..."

# 检查是否安装了Rust
if ! command -v cargo &> /dev/null; then
    echo "错误: 未找到Rust和Cargo"
    echo "请先安装Rust: https://rustup.rs/"
    exit 1
fi

# 构建发布版本
echo "正在编译发布版本..."
cargo build --release

if [ $? -eq 0 ]; then
    echo "构建成功！"
    echo "可执行文件位于: target/release/snake_game"
    echo ""
    echo "运行游戏:"
    echo "  ./target/release/snake_game"
    echo ""
    echo "或者直接运行:"
    echo "  cargo run --release"
else
    echo "构建失败！"
    exit 1
fi
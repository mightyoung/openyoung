#!/bin/bash

echo "启动贪吃蛇游戏..."

# 检查是否已构建
if [ ! -f "target/release/snake_game" ]; then
    echo "未找到已构建的可执行文件，正在构建..."
    ./build.sh
fi

# 运行游戏
echo "正在启动游戏..."
./target/release/snake_game
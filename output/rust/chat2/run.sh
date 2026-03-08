#!/bin/bash

# Rust ChatBot 运行脚本
echo "🔧 构建 Rust ChatBot..."
cargo build

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ 构建成功！"
    echo ""
    echo "🤖 启动聊天机器人..."
    echo "----------------------------------------"
    ./target/debug/chat2
else
    echo "❌ 构建失败，请检查错误信息"
    exit 1
fi
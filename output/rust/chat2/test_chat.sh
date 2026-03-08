#!/bin/bash

# Rust ChatBot 测试脚本
echo "🚀 构建 Rust ChatBot..."
cargo build

echo ""
echo "📋 运行测试对话..."
echo "注意：这是一个交互式程序，需要手动输入命令"
echo ""
echo "建议测试命令："
echo "1. hello"
echo "2. time"
echo "3. date"
echo "4. joke"
echo "5. history"
echo "6. clear"
echo "7. exit"
echo ""
echo "要运行程序，请执行: cargo run"
echo "或直接运行: ./target/debug/chat2"
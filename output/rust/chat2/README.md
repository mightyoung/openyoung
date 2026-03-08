# Rust ChatBot 🤖

一个用 Rust 编写的简单命令行聊天机器人。

## 功能特性

- ✅ 基本对话响应
- ✅ 时间查询功能
- ✅ 日期查询功能  
- ✅ 编程笑话
- ✅ 对话历史记录
- ✅ 历史记录清理
- ✅ 美观的控制台界面

## 安装和运行

### 前提条件
- 安装 [Rust](https://www.rust-lang.org/tools/install)

### 运行步骤

1. **克隆或下载项目**
   ```bash
   cd output/rust/chat2
   ```

2. **构建项目**
   ```bash
   cargo build
   ```

3. **运行聊天机器人**
   ```bash
   cargo run
   ```

4. **直接运行可执行文件**
   ```bash
   # 构建发布版本
   cargo build --release
   
   # 运行
   ./target/release/chat2
   ```

## 可用命令

| 命令 | 描述 |
|------|------|
| `hello` / `hi` | 问候机器人 |
| `time` | 获取当前时间 |
| `date` | 获取当前日期 |
| `joke` | 听一个编程笑话 |
| `history` | 查看对话历史 |
| `clear` | 清除历史记录 |
| `help` | 显示帮助信息 |
| `exit` / `quit` | 退出程序 |

## 示例对话

```
🤖 RUST CHATBOT v1.0
Bot: Hello! I'm Rusty. How can I assist you today?
You: hello
Bot: Hello! How can I help you today?
──────────────────────────────────────────────────
You: time
Bot: Current time is: 14:30:45
──────────────────────────────────────────────────
You: joke
Bot: Why do Rust programmers prefer dark mode? Because light attracts bugs!
──────────────────────────────────────────────────
You: history
Bot: Conversation History:
1. You: hello
   Bot: Hello! How can I help you today?
2. You: time
   Bot: Current time is: 14:30:45
3. You: joke
   Bot: Why do Rust programmers prefer dark mode? Because light attracts bugs!
──────────────────────────────────────────────────
```

## 项目结构

```
chat2/
├── Cargo.toml          # 项目配置和依赖
├── src/
│   └── main.rs        # 主程序文件
└── README.md          # 项目说明文档
```

## 依赖项

- `chrono` - 日期和时间处理
- `rand` - 随机数生成（用于随机笑话）

## 扩展功能建议

1. **添加更多响应** - 在 `responses` 向量中添加更多关键词和响应
2. **文件存储** - 将对话历史保存到文件
3. **网络功能** - 添加简单的 HTTP 服务器支持
4. **AI 集成** - 集成 OpenAI API 或其他 AI 服务
5. **GUI 界面** - 使用 `egui` 或 `iced` 创建图形界面

## 许可证

MIT License
# OpenYoung 使用指南

## 目标
从零开始，部署 OpenYoung 项目，导入 GitHub Agent，并通过飞书与 Agent 对话

---

## 步骤 1: 环境准备

### 1.1 安装依赖

```bash
# 克隆项目
git clone https://github.com/your-repo/openyoung.git
cd openyoung

# 创建虚拟环境 (推荐)
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# 安装依赖
pip install -e .
```

### 1.2 配置环境变量

创建 `.env` 文件:

```bash
# LLM Providers (至少配置一个)
DEEPSEEK_API_KEY=your_deepseek_key
# OPENAI_API_KEY=your_openai_key
# ANTHROPIC_API_KEY=your_anthropic_key

# 飞书配置 (可选)
FEISHU_APP_ID=your_app_id
FEISHU_APP_SECRET=your_app_secret
```

---

### 2.1 使用 openyoung 命令

安装后即可使用 `openyoung` 命令:

```bash
# 查看帮助
openyoung --help

# 查看具体命令帮助
openyoung run --help
openyoung import --help
```

### 2.2 本地运行 (开发模式)

```bash
# 启动 CLI 模式
openyoung run default

# 或启动 REPL 交互模式
openyoung run default -i
```

### 2.2 Docker 部署 (生产模式)

```bash
# 配置环境变量
cp .env.example .env
# 编辑 .env 填入你的 API Keys

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f openyoung
```

---

## 步骤 3: 导入 GitHub Agent

### 3.1 使用 CLI 导入

```bash
# 导入 GitHub Agent (推荐)
openyoung import github https://github.com/FoundationAgents/MetaGPT

# 指定 Agent 名称
openyoung import github https://github.com/FoundationAgents/MetaGPT metagpt

# 增强模式 (带分析和验证)
openyoung import github https://github.com/user/repo my-agent --enhanced

# 快速模式 (跳过验证)
openyoung import github https://github.com/user/repo my-agent --lazy
```

### 3.2 配置 Agent

编辑 `config/agents.yaml`:

```yaml
agents:
  - name: metagpt
    type: primary
    model: deepseek-chat
    github_url: https://github.com/FoundationAgents/MetaGPT
```

---

## 步骤 4: 配置飞书通信

### 4.1 创建飞书应用

1. 访问 [飞书开放平台](https://open.feishu.cn/)
2. 创建企业自建应用
3. 获取 `App ID` 和 `App Secret`
4. 添加权限:
   - `im:message:send_as_bot`
   - `im:message:receive`

### 4.2 配置 Webhook

```bash
# 在飞书后台创建机器人，获取 Webhook 地址
# 格式: https://open.feishu.cn/open-apis/bot/v2/hook/xxxxx
```

### 4.3 使用 CLI 配置通道

```bash
# 初始化 (推荐首次使用)
openyoung init

# 查看可用通道
openyoung channel list

# 显示当前通道配置
openyoung channel config show

# 添加飞书通道
openyoung channel config add feishu --app-id YOUR_APP_ID --app-secret YOUR_APP_SECRET

# 启用通道
openyoung channel config enable feishu

# 启动通道服务
openyoung channel start
```

---

## 步骤 5: 与 Agent 对话

### 5.1 通过终端

```bash
# 单次执行
openyoung run default "帮我开发一个 Rust IM 程序"

# 交互式 REPL 模式
openyoung run default -i
# 输入你的问题，输入 exit 退出
```

### 5.2 通过飞书

1. 在飞书群聊中添加机器人
2. @机器人 发送问题
3. 机器人自动回复

---

## 步骤 6: 开发 Rust IM 程序

### 6.1 提出需求

告诉 Agent 你的需求:

```
我想开发一个 IM (即时通讯) 程序
- 语言: Rust
- 功能: 私聊、群聊
- 协议: WebSocket
- 目标: 轻量、高性能
```

### 6.2 Agent 会帮你

1. 生成项目架构
2. 编写核心代码
3. 配置依赖
4. 编写测试

---

## 快速启动命令汇总

```bash
# 1. 克隆项目
git clone https://github.com/your-repo/openyoung.git
cd openyoung

# 2. 安装依赖
pip install -e .

# 3. 初始化 (推荐)
openyoung init

# 4. 导入 Agent
openyoung import github https://github.com/FoundationAgents/MetaGPT

# 5. 开始对话
openyoung run default "帮我用 Rust 开发一个 IM 程序"
```

---

## 完整 CLI 命令参考

### 基础命令

| 命令 | 说明 |
|------|------|
| `openyoung --help` | 查看帮助 |
| `openyoung --version` | 查看版本 |
| `openyoung init` | 初始化配置 (交互式向导) |
| `openyoung run <agent> [task]` | 运行 Agent |
| `openyoung run <agent> -i` | 交互式 REPL 模式 |

### 通道管理 (Channel)

| 命令 | 说明 |
|------|------|
| `openyoung channel list` | 列出可用通道 |
| `openyoung channel config show` | 显示通道配置 |
| `openyoung channel config add <platform>` | 添加通道 |
| `openyoung channel config remove <platform>` | 移除通道 |
| `openyoung channel config enable <platform>` | 启用通道 |
| `openyoung channel config disable <platform>` | 禁用通道 |
| `openyoung channel start` | 启动通道服务 |

支持的平台: `cli`, `telegram`, `discord`, `qq`, `dingtalk`, `feishu`

### 导入命令 (Import)

| 命令 | 说明 |
|------|------|
| `openyoung import github <url>` | 从 GitHub 导入 |
| `openyoung import github <url> <name>` | 导入并指定名称 |

### Agent 管理

| 命令 | 说明 |
|------|------|
| `openyoung agent list` | 列出可用 Agent |
| `openyoung agent info <name>` | 查看 Agent 信息 |
| `openyoung agent use <name>` | 设置默认 Agent |

### LLM Provider 管理

| 命令 | 说明 |
|------|------|
| `openyoung llm list` | 列出 LLM Provider |
| `openyoung llm add <provider> --api-key <key>` | 添加 Provider |
| `openyoung llm remove <provider>` | 移除 Provider |
| `openyoung llm use <provider>` | 设置默认 Provider |
| `openyoung llm info [provider]` | 查看 Provider 信息 |

支持的 Provider: `deepseek`, `openai`, `anthropic`, `moonshot`, `qwen`, `glm`

### 配置管理

| 命令 | 说明 |
|------|------|
| `openyoung config list` | 列出所有配置 |
| `openyoung config get <key>` | 获取配置值 |
| `openyoung config set <key> <value>` | 设置配置值 |

### 评估命令

| 命令 | 说明 |
|------|------|
| `openyoung eval history [agent]` | 查看评估历史 |
| `openyoung eval trend [agent]` | 查看评估趋势 |

### 其他命令

| 命令 | 说明 |
|------|------|
| `openyoung package list` | 列出已安装的包 |
| `openyoung package create <name>` | 创建新 Agent 模板 |
| `openyoung subagent list` | 列出 SubAgent |
| `openyoung mcp servers` | 列出 MCP 服务器 |
| `openyoung memory search <query>` | 搜索记忆 |
| `openyoung templates list` | 列出模板市场 |

---

## 故障排除

| 问题 | 解决方案 |
|------|----------|
| LLM API 错误 | 检查 .env 中的 API Key |
| 飞书连接失败 | 确认 Webhook URL 正确 |
| 导入 Agent 失败 | 检查 GitHub URL 是否可访问 |
| Docker 启动失败 | 检查端口是否被占用 |

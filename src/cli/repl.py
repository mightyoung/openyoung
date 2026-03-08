"""
OpenYoung Interactive REPL
类似 Claude Code / OpenCode 的交互式命令行界面
"""

from datetime import datetime
from pathlib import Path

# 尝试导入 prompt_toolkit，如果失败则使用简单模式
try:
    from prompt_toolkit import PromptSession
    from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
    from prompt_toolkit.completion import WordCompleter
    from prompt_toolkit.history import InMemoryHistory
    from prompt_toolkit.styles import Style

    PROMPT_TOOLKIT_AVAILABLE = True
except ImportError:
    PROMPT_TOOLKIT_AVAILABLE = False

# 样式定义
STYLE = Style.from_dict(
    {
        "prompt": "#00ff00 bold",
        "user-input": "#ffffff",
        "assistant": "#00ffff",
        "error": "#ff0000 bold",
        "info": "#888888",
        "header": "#ffff00 bold",
    }
)


class OpenYoungREPL:
    """OpenYoung 交互式 REPL

    特性:
    - 类似 Claude Code 的界面
    - 上下文记忆
    - 命令补全
    - 会话历史
    - 优雅退出
    """

    def __init__(self, agent_name: str = "default", model: str | None = None):
        self.agent_name = agent_name
        self.model = model
        self.agent = None
        self.messages: list[dict[str, str]] = []
        self.session_start = datetime.now()
        self.running = True

        if PROMPT_TOOLKIT_AVAILABLE:
            # 创建 prompt session
            self.history = InMemoryHistory()
            self.completer = WordCompleter(
                [
                    "exit",
                    "quit",
                    "help",
                    "clear",
                    "history",
                    "model",
                    "reset",
                    "verbose",
                    "short",
                ]
            )
            self.session = PromptSession(
                history=self.history,
                auto_suggest=AutoSuggestFromHistory(),
                completer=self.completer,
                style=STYLE,
            )

    async def initialize(self):
        """初始化 Agent"""
        from src.agents.young_agent import YoungAgent

        # 加载配置
        config = self._load_config()

        # 覆盖模型
        if self.model:
            config.model = self.model

        # 创建 Agent
        self.agent = YoungAgent(config)

        # 添加系统消息
        self.messages.append(
            {
                "role": "system",
                "content": f"OpenYoung Agent '{self.agent_name}' 已启动。当前时间: {self.session_start.isoformat()}",
            }
        )

        self._print_welcome()

    def _load_config(self) -> "AgentConfig":
        """加载 Agent 配置"""
        from src.core.types import AgentConfig, AgentMode

        # 尝试加载 YAML 配置
        agent_file = Path(__file__).parent.parent / "agents" / f"{self.agent_name}.yaml"

        if agent_file.exists():
            try:
                import yaml

                with open(agent_file) as f:
                    cfg = yaml.safe_load(f)

                model_cfg = cfg.get("model", {})
                return AgentConfig(
                    name=cfg.get("name", self.agent_name),
                    mode=AgentMode.PRIMARY,
                    model=model_cfg.get("model", "deepseek-chat"),
                    temperature=model_cfg.get("temperature", 0.7),
                    max_tokens=model_cfg.get("max_tokens"),
                    system_prompt=cfg.get("description", "你是一个有帮助的AI助手。"),
                )
            except ImportError:
                pass

        # 默认配置
        return AgentConfig(
            name=self.agent_name,
            mode=AgentMode.PRIMARY,
            model="deepseek-chat",
            temperature=0.7,
        )

    def _print_welcome(self):
        """打印欢迎信息"""
        print("\n" + "=" * 50)
        print("  🚀 OpenYoung Agent")
        print("=" * 50)
        print(f"  Agent: {self.agent_name}")
        print(f"  Model: {self.agent.config.model}")
        print(f"  Session: {self.session_start.strftime('%Y-%m-%d %H:%M:%S')}")
        print("-" * 50)
        print("  输入你的请求，或输入 help 查看命令")
        print("  输入 exit/quit 退出")
        print("=" * 50 + "\n")

    def _print_prompt(self) -> str:
        """打印提示符"""
        return "\n\033[92mopenyoung\033[0m > "

    async def run(self):
        """运行 REPL"""
        await self.initialize()

        while self.running:
            try:
                if PROMPT_TOOLKIT_AVAILABLE:
                    # 获取用户输入
                    user_input = await self.session.prompt_async(self._print_prompt())
                else:
                    # 简单模式
                    user_input = input(self._print_prompt())

                # 处理输入
                await self._process_input(user_input)

            except KeyboardInterrupt:
                # Ctrl+C 继续
                print("\n(使用 'exit' 或 'quit' 退出)")
                continue
            except EOFError:
                # Ctrl+D 退出
                break

        self._print_goodbye()

    async def _process_input(self, user_input: str):
        """处理用户输入"""
        user_input = user_input.strip()

        if not user_input:
            return

        # 添加到历史
        if PROMPT_TOOLKIT_AVAILABLE:
            self.history.append_string(user_input)

        # 命令处理
        if user_input.lower() in ["exit", "quit", "q"]:
            self.running = False
            return

        if user_input.lower() == "help":
            self._print_help()
            return

        if user_input.lower() == "clear":
            print("\n" + "\n" * 50)
            return

        if user_input.lower() == "history":
            self._print_history()
            return

        if user_input.lower() == "reset":
            self._reset_session()
            return

        if user_input.lower().startswith("model "):
            self._change_model(user_input[6:].strip())
            return

        # 执行任务
        await self._execute_task(user_input)

    async def _execute_task(self, task: str):
        """执行 AI 任务"""
        print("\n[处理请求...]")

        try:
            # 调用 Agent
            response = await self.agent.run(task)

            # 打印响应
            print(f"\n\033[96m{response}\033[0m\n")

            # 添加到消息历史
            self.messages.append({"role": "user", "content": task})
            self.messages.append({"role": "assistant", "content": response})

        except Exception as e:
            print(f"\n\033[91m错误: {str(e)}\033[0m\n")

    def _print_help(self):
        """打印帮助信息"""
        print("""
\033[93m可用命令:\033[0m
  help     - 显示帮助信息
  clear    - 清除屏幕
  history  - 显示对话历史
  reset    - 重置会话
  model    - 切换模型 (如: model gpt-4)
  exit/quit - 退出程序

\033[93m快捷键:\033[0m
  Ctrl+C  - 取消输入
  Ctrl+D  - 退出程序
  Ctrl+R  - 历史搜索
  ↑↓      - 历史导航
""")

    def _print_history(self):
        """打印对话历史"""
        print("\n\033[93m对话历史:\033[0m")
        for i, msg in enumerate(self.messages[-10:], 1):
            role = "用户" if msg["role"] == "user" else "助手"
            content = msg["content"][50:] + "..." if len(msg["content"]) > 50 else msg["content"]
            print(f"  {i}. [{role}]: {content}")
        print()

    def _reset_session(self):
        """重置会话"""
        self.messages.clear()
        if hasattr(self.agent, "_history"):
            self.agent._history.clear()
        print("\n\033[92m会话已重置\033[0m\n")

    def _change_model(self, model: str):
        """切换模型"""
        if self.agent:
            self.agent.config.model = model
            print(f"\n\033[92m已切换到模型: {model}\033[0m\n")

    def _print_goodbye(self):
        """打印告别信息"""
        duration = datetime.now() - self.session_start
        print(f"""
\033[93m会话结束\033[0m
  持续时间: {duration}
  消息数: {len(self.messages)}
  感谢使用 OpenYoung!
""")


async def start_repl(agent_name: str = "default", model: str | None = None):
    """启动 REPL"""
    repl = OpenYoungREPL(agent_name, model)
    await repl.run()

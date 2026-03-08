---
name: github-import
description: |
  从 GitHub 或其他 Git 仓库导入 Agent 配置到本地。**务必使用此技能**当用户提到：导入 GitHub 仓库、克隆 agent 配置、拉取代码作为 agent、从 GitHub 下载 agent 模板、配置 GitHub 项目成本地 agent、使用 import github 命令、将仓库配置为 OpenYoung agent、下载 AI agent 项目、克隆 agent 模板到本地。自动完成 git clone、项目分析、配置文件解析、FlowSkill 生成、Agent 和 SubAgent 库构建。
compatibility:
  tools:
    - read
    - write
    - edit
    - bash
    - glob
    - grep
  dependencies:
    - httpx
    - pyyaml
    - git
---

# GitHub Agent 导入器

将 GitHub 或其他 Git 仓库中的高质量 Agent 模板自动配置到本地项目。

## 使用场景

当用户想要：
- 从 GitHub 导入 Agent 模板
- 克隆并配置 GitHub 上的 agent 配置
- 将 GitHub 仓库中的 CLAUDE.md、AGENTS.md 配置到本地
- 导入 MCP、Hooks、Skills 配置

## 执行流程

### Step 1: 解析 GitHub URL

支持多种 URL 格式：
- `https://github.com/owner/repo`
- `github.com/owner/repo`
- `owner/repo`

```python
def _parse_github_url(url: str) -> tuple:
    url = url.strip().rstrip("/")
    if "github.com" in url:
        parts = url.split("github.com/")[-1].split("/")
    else:
        parts = url.split("/")
    if len(parts) >= 2:
        return parts[0], parts[1]
    return None, None
```

### Step 2: Git Clone 仓库

将仓库克隆到 `/tmp/openyoung_imports/` 目录：

```python
import subprocess

def _git_clone(self, owner: str, repo: str) -> Path:
    repo_url = f"https://github.com/{owner}/{repo}.git"
    local_path = self.temp_dir / f"{owner}_{repo}"

    if local_path.exists():
        shutil.rmtree(local_path)

    result = subprocess.run(
        ["git", "clone", "--depth", "1", repo_url, str(local_path)],
        capture_output=True, text=True, timeout=120
    )
    if result.returncode == 0:
        return local_path
    return None
```

### Step 3: 分析项目结构

扫描仓库，识别关键文件：

| 文件类型 | 检测文件 |
|---------|---------|
| 主提示词 | CLAUDE.md |
| 子代理配置 | AGENTS.md |
| Skills | skills/*.yaml, skills/*.json |
| MCPs | mcp.json, .mcp.json |
| Hooks | hooks.json, .cursor/hooks.json |
| Evaluations | eval*.yaml, *eval*.yaml |

```python
def _analyze_project_structure(self, local_path: Path) -> Dict:
    structure = {
        "languages": [],
        "has_claude_md": False,
        "has_agents_md": False,
        "has_skills": False,
        "has_mcps": False,
        "has_hooks": False,
        "has_evaluation": False,
        "skills": [],
        "mcps": [],
        "hooks": [],
        "evaluations": [],
        "main_prompt": "",
        "subagent_prompts": [],
    }

    for item in local_path.rglob("*"):
        if item.is_file():
            name = item.name.lower()
            if name == "claude.md":
                structure["has_claude_md"] = True
                structure["main_prompt"] = item.read_text()[:5000]
            elif name == "agents.md":
                structure["has_agents_md"] = True
                structure["subagent_prompts"] = self._parse_agents_md(item)
            # ... 检测其他文件类型
```

### Step 4: 生成 FlowSkill

FlowSkill 描述 Agent 的执行流程和触发条件：

```python
def _generate_flowskill(self, local_path: Path, structure: Dict) -> FlowSkill:
    return FlowSkill(
        name=f"flow-{language}",
        description=self._extract_flow_description(main_prompt),
        trigger_conditions=self._extract_triggers(main_prompt),
        required_skills=structure.get("skills", []),
        required_mcps=structure.get("mcps", []),
        required_evaluations=structure.get("evaluations", []),
        subagent_calls=self._extract_subagent_calls(subagent_prompts),
    )
```

### Step 5: 解析配置文件

解析并收集各类配置文件：

```python
def _parse_configs(self, local_path: Path) -> Dict:
    configs = {"skills": [], "mcps": [], "hooks": [], "evaluations": []}

    # 解析 skills
    for item in local_path.rglob("skill*.yaml"):
        config = yaml.safe_load(item.read_text())
        configs["skills"].append({"path": str(item), "config": config})

    # 解析 mcp.json
    for item in local_path.rglob("mcp.json"):
        config = json.loads(item.read_text())
        configs["mcps"].append({"path": str(item), "config": config})

    return configs
```

### Step 6: 创建 Agent 配置

生成 `packages/{agent-name}/agent.yaml`：

```python
def _create_agent_config(self, owner, repo, agent_name, structure, flowskill, configs):
    agent_config = {
        "name": agent_name,
        "version": "1.0.0",
        "description": f"Imported from {owner}/{repo}",
        "source_url": f"https://github.com/{owner}/{repo}",
        "model": {"name": "deepseek-chat", "temperature": 0.7},
        "tools": ["read", "write", "edit", "bash", "glob", "grep"],
        "skills": [],
        "mcps": [],
        "sub_agents": [],
        "flowskill": flowskill,
        "system_prompt": structure.get("main_prompt", "")[:4000],
    }

    # 保存到 packages/{agent_name}/agent.yaml
```

### Step 7: 创建 SubAgent 库

自动提取并保存 SubAgent 到 `subagents/` 目录：

```python
# 为每个 SubAgent 创建独立配置
for sa_prompt in structure.get("subagent_prompts", []):
    subagent = SubAgentBinding(
        name=sa_prompt.get("name"),
        type="general",
        description=sa_prompt.get("description"),
    )

    # 保存到 subagents/{name}/agent.yaml
    subagent_dir = self.subagents_dir / subagent.name
    with open(subagent_dir / "agent.yaml", "w") as f:
        yaml.dump(asdict(subagent), f)
```

## MCP 智能加载机制

在 Agent 加载前，自动检测并启动所需的 MCP Server：

```python
def check_and_start_mcp(mcp_name: str) -> MCPConnectionResult:
    # Step 1: 检查进程是否已运行
    if mcp_name in running_servers:
        return connected

    # Step 2: 尝试 MCP 协议检测连接
    if probe_mcp_connection(mcp_name):
        return connected

    # Step 3: 尝试启动 MCP Server
    if start_mcp_server(mcp_name):
        return connected

    # Step 4: 启动失败，跳过继续执行 (不报错)
    return not_connected
```

## 输出结构

导入完成后，生成以下文件结构：

```
{project}/
├── packages/
│   └── {agent-name}/
│       ├── agent.yaml          # Agent 主配置
│       └── original/           # 原始配置文件
│           └── CLAUDE.md
├── subagents/
│   ├── {subagent-name1}/
│   │   └── agent.yaml
│   └── {subagent-name2}/
│       └── agent.yaml
```

## 使用命令

```bash
# 完整克隆导入 (推荐 - 包含仓库所有文件)
# 仓库会完整克隆到 packages/<agent>/original/ 目录
openyoung import github https://github.com/affaan-m/everything-claude-code my-agent --no-lazy

# 快速克隆 (仅获取配置，不克隆完整仓库)
openyoung import github https://github.com/owner/repo --lazy

# 增强导入 (默认，包含分析)
openyoung import github https://github.com/affaan-m/everything-claude-code my-agent

# 基础导入 (仅 API 获取)
openyoung import github https://github.com/owner/repo --basic

# 列出已导入的 SubAgents
openyoung subagent list

# 启动 MCP Server
openyoung mcp start <server-name>

# 运行 Agent
openyoung run my-agent "Hello"
```

## 完整克隆模式详解

使用 `--no-lazy` 选项时：

1. **仓库克隆**: 完整克隆到 `packages/<agent>/original/`
2. **文件结构**: 保留仓库原始目录结构
3. **配置引用**: agent.yaml 中引用的 skills/mcps 文件路径指向 `original/` 目录
4. **优点**:
   - 所有配置文件都存在于本地
   - 可离线使用
   - 配置完整可追溯

### 输出结构

```
packages/<agent>/
├── agent.yaml          # Agent 主配置
├── original/           # 完整克隆的仓库
│   ├── plugins/
│   ├── skills/
│   ├── commands/
│   ├── .agents/
│   └── ...
└── subagents/         # 子 Agent 配置
```

## 错误处理

- **Git clone 超时**: 回退到 API 方式获取文件
- **MCP 启动失败**: 跳过继续执行，不阻塞 Agent 加载
- **配置文件解析失败**: 记录警告但继续处理其他文件

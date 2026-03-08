GitHub Repository Importer
从 GitHub 仓库自动分析并导入 Agent 配置

## Classes

### `GitHubFile`

GitHub 文件

### `GitHubImporter`

GitHub 仓库导入器

**Methods:**
- `import_from_url`

## Functions

### `import_github()`

从 GitHub 导入 (CLI 入口)

### `import_from_url()`

从 GitHub URL 导入

Args:
    github_url: GitHub 仓库 URL (如 https://github.com/affaan-m/everything-claude-code)
    agent_name: 可选的 Agent 名称

Returns:
    导入结果

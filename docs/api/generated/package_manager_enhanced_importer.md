GitHub Repository Importer (Enhanced)
增强版 GitHub 仓库导入器 - 支持 git clone + agent 分析
支持 GitHub、GitLab、Gitee 等多种 git 仓库

## Classes

### `GitHubFile`

GitHub 文件

### `FlowSkill`

FlowSkill 配置 - Agent 执行流程

### `EnhancedGitHubImporter`

增强版 GitHub 仓库导入器

**Methods:**
- `import_from_url`

## Functions

### `import_github_enhanced()`

从 GitHub 导入 (增强版 CLI 入口)

### `import_from_url()`

从 Git/GitLab/Gitee URL 导入

Args:
    url: 仓库 URL (GitHub/GitLab/Gitee)
    agent_name: 可选的 Agent 名称
    use_git_clone: 是否使用 git clone (更完整)
    analyze_with_agent: 是否使用 agent 分析代码
    validate: 是否执行导入后验证
    lazy_clone: 是否延迟 clone（仅获取元数据，不完整克隆）

Returns:
    导入结果

Git Importer - 通用 Git 仓库导入器接口
支持 GitHub、GitLab、Gitee 等 git 仓库

## Classes

### `GitImporter`

通用 Git 仓库导入器抽象基类

**Methods:**
- `get_host_name`
- `parse_url`
- `get_clone_url`
- `get_api_url`
- `clone`
- `get_file_content`
- `list_files`

### `GitHubImporter`

GitHub 仓库导入器

**Methods:**
- `get_host_name`
- `parse_url`
- `get_clone_url`
- `get_api_url`

### `GitLabImporter`

GitLab 仓库导入器

**Methods:**
- `get_host_name`
- `parse_url`
- `get_clone_url`
- `get_api_url`

### `GiteeImporter`

Gitee 仓库导入器

**Methods:**
- `get_host_name`
- `parse_url`
- `get_clone_url`
- `get_api_url`

### `GitImporterFactory`

Git 导入器工厂

**Methods:**
- `create`
- `from_url`

## Functions

### `get_host_name()`

获取仓库主机名

### `parse_url()`

解析仓库 URL

Returns:
    Tuple[host, owner, repo] 或 None

### `get_clone_url()`

获取克隆 URL

### `get_api_url()`

获取 API URL

### `clone()`

克隆仓库到本地

### `get_file_content()`

从本地克隆获取文件内容

### `list_files()`

列出仓库中的文件

### `get_host_name()`

### `parse_url()`

解析 GitHub URL

### `get_clone_url()`

### `get_api_url()`

### `get_host_name()`

### `parse_url()`

解析 GitLab URL

### `get_clone_url()`

### `get_api_url()`

### `get_host_name()`

### `parse_url()`

解析 Gitee URL

### `get_clone_url()`

### `get_api_url()`

### `create()`

根据主机名创建导入器

### `from_url()`

从 URL 自动识别并创建导入器

Returns:
    Tuple[importer, host, owner, repo] 或 None

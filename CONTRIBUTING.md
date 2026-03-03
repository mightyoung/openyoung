# Contributing to OpenYoung / 贡献指南

[English](#english) | [中文](#中文)

---

## English

### Welcome

Thank you for considering contributing to OpenYoung! This document provides guidelines for contributing to this project.

### Code of Conduct

- Be respectful and inclusive
- Welcome newcomers and help them learn
- Provide constructive feedback
- Focus on what is best for the community

### How to Contribute

#### Reporting Bugs

1. Check if the bug has already been reported
2. Create a detailed bug report including:
   - Clear title and description
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details

#### Suggesting Features

1. Check existing issues and PRs
2. Provide a clear feature description
3. Explain why this feature would be useful
4. Include any relevant examples or mockups

#### Pull Requests

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make your changes and commit: `git commit -m 'Add some feature'`
4. Push to the branch: `git push origin feature/your-feature`
5. Submit a Pull Request

### Development Setup

```bash
# Clone the repository
git clone https://github.com/mightyoung/openyoung.git
cd openyoung

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .

# Install dev dependencies
pip install pytest ruff black

# Run tests
pytest tests/

# Run linter
ruff check src/
```

### Coding Standards

- Follow PEP 8 style guide
- Use type hints where possible
- Write docstrings for all public functions
- Keep functions small and focused
- Write meaningful commit messages

### Commit Message Format

```
type(scope): description

[optional body]
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

### Questions?

- Open an issue for questions
- Join our community discussions

---

## 中文

### 欢迎

感谢您考虑为 OpenYoung 贡献力量！本文档提供向本项目贡献的指南。

### 行为准则

- 尊重和包容
- 欢迎新手并帮助他们学习
- 提供建设性的反馈
- 关注社区的最佳利益

### 如何贡献

#### 报告 Bug

1. 检查 Bug 是否已被报告
2. 创建详细的 Bug 报告，包括：
   - 清晰的标题和描述
   - 重现步骤
   - 预期与实际行为
   - 环境详情

#### 功能建议

1. 查看现有的 issues 和 PRs
2. 提供清晰的功能描述
3. 解释为什么这个功能会有用
4. 包括任何相关的示例或模型

#### 提交 Pull Request

1. Fork 仓库
2. 创建功能分支：`git checkout -b feature/你的功能`
3. 进行修改并提交：`git commit -m '添加某功能'`
4. 推送到分支：`git push origin feature/你的功能`
5. 提交 Pull Request

### 开发环境设置

```bash
# 克隆仓库
git clone https://github.com/mightyoung/openyoung.git
cd openyoung

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows 上: venv\Scripts\activate

# 安装依赖
pip install -e .

# 安装开发依赖
pip install pytest ruff black

# 运行测试
pytest tests/

# 运行代码检查
ruff check src/
```

### 代码规范

- 遵循 PEP 8 风格指南
- 尽可能使用类型提示
- 为所有公共函数编写文档字符串
- 保持函数小而专注
- 编写有意义的提交信息

### 提交信息格式

```
类型(范围): 描述

[可选正文]
```

类型：`feat`、`fix`、`docs`、`style`、`refactor`、`test`、`chore`

### 问题？

- 开启 issue 提问
- 加入我们的社区讨论

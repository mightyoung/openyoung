# PEAS Contribution Guide

## 欢迎贡献

感谢您对PEAS项目的兴趣！我们欢迎各种形式的贡献，包括：
- 代码改进
- 文档完善
- Bug修复
- 新功能开发
- 测试用例

## 开发环境设置

### 1. 克隆项目

```bash
git clone https://github.com/your-repo/openyoung.git
cd openyoung
```

### 2. 安装依赖

```bash
pip install -e .
pip install pytest pytest-asyncio
```

### 3. 运行测试

```bash
# 运行所有PEAS测试
pytest tests/peas/ -v

# 运行特定测试
pytest tests/peas/test_parser.py -v

# 带覆盖率
pytest tests/peas/ --cov=src.peas --cov-report=html
```

## 代码规范

### Python风格

- 遵循PEP 8
- 使用类型注解
- 文档字符串使用Google风格

### 命名规范

```python
# 类名: 大驼峰
class FeatureTracker:
    pass

# 函数/方法: 小写下划线
def parse_markdown(content: str) -> ParsedDocument:
    pass

# 常量: 全大写下划线
MAX_CONTENT_SIZE = 10 * 1024 * 1024
```

### 类型注解

```python
from typing import Optional, list

def verify(
    self,
    execution_result: str,
    llm_client: Optional[Any] = None
) -> list[FeatureStatus]:
    """验证执行结果

    Args:
        execution_result: 执行结果文本
        llm_client: 可选的LLM客户端

    Returns:
        功能点状态列表
    """
    pass
```

## 目录结构

```
src/peas/
├── __init__.py          # 公共API导出
├── types/               # 数据类型
│   ├── document.py      # 文档类型
│   ├── contract.py      # 合约类型
│   └── verification.py # 验证类型
├── understanding/       # 理解层
│   ├── markdown_parser.py
│   └── intent_extractor.py
├── contract/           # 合约构建
│   └── builder.py
├── verification/       # 验证追踪
│   ├── tracker.py
│   └── drift_detector.py
└── integration/        # 外部集成
    └── harness.py
```

## 提交规范

### Commit Message格式

```
type(scope): description

[optional body]
```

类型:
- `feat`: 新功能
- `fix`: Bug修复
- `docs`: 文档更新
- `test`: 测试用例
- `refactor`: 代码重构
- `perf`: 性能优化

示例:
```
feat(parser): 添加优先级检测支持中文

添加对中文关键词的支持：
- 必须 -> MUST
- 应该 -> SHOULD
- 可以 -> COULD

Fixes #123
```

## Pull Request流程

### 1. 创建分支

```bash
git checkout -b feature/your-feature
# 或
git checkout -b fix/issue-description
```

### 2. 开发

- 编写代码
- 添加测试
- 更新文档

### 3. 提交

```bash
git add src/peas/your_changes.py
git commit -m "feat: add new feature"
```

### 4. 推送

```bash
git push origin feature/your-feature
```

### 5. 创建PR

在GitHub上创建Pull Request，描述：
- 解决的问题
- 实现方案
- 测试结果

## 测试指南

### 单元测试

```python
# tests/peas/test_parser.py
import pytest
from src.peas import MarkdownParser, Priority

def test_parse_title():
    parser = MarkdownParser()
    doc = parser.parse("# Test Title\n\nContent")

    assert doc.title == "Test Title"

def test_parse_priority():
    parser = MarkdownParser()
    doc = parser.parse("""
# Test

- Feature: Test Feature
- Must: Required
    """)

    fp = doc.feature_points[0]
    assert fp.priority == Priority.MUST
```

### 集成测试

```python
# tests/peas/test_e2e.py
import pytest
from src.peas import (
    MarkdownParser,
    ContractBuilder,
    FeatureTracker,
    DriftDetector,
)

@pytest.mark.asyncio
async def test_full_workflow():
    # 解析
    parser = MarkdownParser()
    doc = parser.parse PRD_CONTENT

    # 构建
    builder = ContractBuilder()
    contract = builder.build(doc)

    # 验证
    tracker = FeatureTracker(contract)
    results = tracker.verify_sync("实现代码...")

    # 偏离检测
    detector = DriftDetector()
    report = detector.detect(results, contract)

    assert report.alignment_rate > 0
```

### 运行特定测试

```bash
# 只运行parser测试
pytest tests/peas/test_parser.py -v

# 只运行e2e测试
pytest tests/peas/test_e2e.py -v

# 运行带async的测试
pytest tests/peas/ -v --asyncio-mode=auto
```

## 文档贡献

### 添加新功能文档

1. 更新API Reference
2. 添加使用示例
3. 更新教程

### 文档格式

```markdown
### 函数名

描述函数作用

```python
# 示例代码
result = function(param)
```

参数:
- `param`: 参数说明

返回:
- 返回值说明
```

## 常见问题

### Q: 如何添加新的验证方法?

A: 在`FeatureTracker`中添加新方法：

```python
def _custom_verify(
    self,
    req: ContractRequirement,
    execution: str
) -> FeatureStatus:
    # 实现你的验证逻辑
    pass
```

### Q: 如何支持新的文档格式?

A: 在`understanding`模块中添加新的Parser：

```python
class NewFormatParser:
    def parse(self, content: str) -> ParsedDocument:
        # 实现解析逻辑
        pass
```

### Q: 测试失败怎么办?

A:
1. 检查测试用例是否正确
2. 检查实现是否符合预期
3. 运行完整测试套件确认影响范围
4. 提交修复

## 联系方式

- 问题: GitHub Issues
- 讨论: GitHub Discussions
- 贡献: 提交Pull Request

## 许可证

MIT License - 详见LICENSE文件

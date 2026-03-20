# MarkdownParser

Parses markdown documents into structured PEAS components.

## Overview

MarkdownParser transforms raw markdown content into a normalized intermediate representation suitable for intent extraction and drift detection.

## Class Signature

```python
class MarkdownParser:
    def __init__(self, config: ParserConfig | None = None)
    def parse(self, content: str) -> ParsedDocument
    def parse_file(self, path: str) -> ParsedDocument
```

## Methods

### parse

```python
def parse(self, content: str) -> ParsedDocument
```

Parses markdown content into a structured document.

**Parameters:**
- `content` (str): Raw markdown string

**Returns:**
- `ParsedDocument`: Structured document with sections, code blocks, and metadata

### parse_file

```python
def parse_file(self, path: str) -> ParsedDocument
```

Parses a markdown file from disk.

**Parameters:**
- `path` (str): Path to markdown file

**Returns:**
- `ParsedDocument`: Structured document

## Usage Example

```python
from peas.api import MarkdownParser

parser = MarkdownParser()
document = parser.parse_file("specification.md")

for section in document.sections:
    print(f"Section: {section.heading}")
    print(f"Content: {section.content[:100]}...")
```

## Configuration

```python
@dataclass
class ParserConfig:
    strip_comments: bool = True
    extract_code_blocks: bool = True
    preserve_whitespace: bool = False
```

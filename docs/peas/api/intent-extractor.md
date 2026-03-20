# IntentExtractor

Extracts structured intents from parsed documents.

## Overview

IntentExtractor analyzes parsed markdown documents to identify and extract user intents, goals, and actionable requirements.

## Class Signature

```python
class IntentExtractor:
    def __init__(self, model: LLMClient | None = None)
    def extract(self, document: ParsedDocument) -> List[Intent]
    def extract_from_text(self, text: str) -> List[Intent]
```

## Methods

### extract

```python
def extract(self, document: ParsedDocument) -> List[Intent]
```

Extracts intents from a parsed document.

**Parameters:**
- `document` (ParsedDocument): Parsed markdown document

**Returns:**
- `List[Intent]`: List of extracted intents

### extract_from_text

```python
def extract_from_text(self, text: str) -> List[Intent]
```

Extracts intents directly from raw text.

**Parameters:**
- `text` (str): Raw text content

**Returns:**
- `List[Intent]`: List of extracted intents

## Intent Structure

```python
@dataclass
class Intent:
    id: str
    type: IntentType
    description: str
    confidence: float
    requirements: List[str]
    constraints: List[str]
```

## Usage Example

```python
from peas.api import IntentExtractor, MarkdownParser

parser = MarkdownParser()
extractor = IntentExtractor()

document = parser.parse_file("requirements.md")
intents = extractor.extract(document)

for intent in intents:
    print(f"[{intent.type}] {intent.description}")
    print(f"  Confidence: {intent.confidence}")
    print(f"  Requirements: {intent.requirements}")
```

## Intent Types

- `IntentType.ACTION` - Actionable task or command
- `IntentType.QUESTION` - Question requiring clarification
- `IntentType.CONSTRAINT` - System constraint or requirement
- `IntentType.GOAL` - High-level objective

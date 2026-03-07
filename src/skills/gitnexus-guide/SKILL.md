---
name: gitnexus-guide
description: "Use when the user asks about GitNexus itself — available tools, how to query the knowledge graph, MCP resources, graph schema, or workflow reference. Examples: 'What GitNexus tools are available?', 'How do I use GitNexus?', '帮助'"
trigger_patterns:
  - "help"
  - "帮助"
  - "怎么用"
  - "gitnexus"
  - "tools"
tags:
  - guide
  - reference
requires:
  bins:
    - node
    - npm
    - npx
    - gitnexus
---

# GitNexus Guide

## Overview

GitNexus builds a knowledge graph of your codebase using Tree-sitter AST parsing. It provides AI agents with deep codebase awareness through MCP tools.

## Available Tools

| Tool | Purpose | Example |
|------|---------|---------|
| `list_repos` | List all indexed repos | `list_repos()` |
| `query` | Hybrid search (BM25 + semantic) | `query({query: "auth"})` |
| `context` | 360° symbol view | `context({name: "validateUser"})` |
| `impact` | Blast radius analysis | `impact({target: "X", direction: "upstream"})` |
| `detect_changes` | Git-diff impact | `detect_changes({scope: "staged"})` |
| `rename` | Multi-file rename | `rename({old: "x", new: "y", dry_run: true})` |
| `cypher` | Raw graph queries | `cypher({query: "MATCH..."})` |

## MCP Resources

| Resource | Purpose |
|----------|---------|
| `gitnexus://repos` | List indexed repos |
| `gitnexus://repo/{name}/context` | Stats + staleness |
| `gitnexus://repo/{name}/clusters` | Functional areas |
| `gitnexus://repo/{name}/processes` | Execution flows |
| `gitnexus://repo/{name}/process/{name}` | Full trace |
| `gitnexus://repo/{name}/schema` | Graph schema |

## Common Workflows

### Understanding Code
1. `READ gitnexus://repo/{name}/context` — overview
2. `gitnexus_query({query: "concept"})` — find flows
3. `gitnexus_context({name: "symbol"})` — deep dive

### Impact Analysis
1. `gitnexus_impact({target: "symbol", direction: "upstream"})`
2. Assess risk (d=1 = WILL BREAK)
3. Report to user

### Safe Refactoring
1. `gitnexus_impact` — find all callers
2. `gitnexus_rename({dry_run: true})` — preview
3. Review text edits manually
4. Execute with `dry_run: false`

## Risk Levels

| Depth | Meaning | Action |
|-------|---------|--------|
| d=1 | WILL BREAK | Update all callers |
| d=2 | LIKELY AFFECTED | Run tests |
| d=3 | MAY NEED TESTING | Verify critical paths |

## Quick Reference

```bash
# Index repo
npx gitnexus analyze

# Check status
npx gitnexus status

# Update index
npx gitnexus analyze --skip-embeddings

# Generate wiki
npx gitnexus wiki
```

## Installation

```bash
npm install -g gitnexus
cd your-project
npx gitnexus analyze
```

For Claude Code:
```bash
claude mcp add gitnexus -- npx -y gitnexus@latest mcp
```

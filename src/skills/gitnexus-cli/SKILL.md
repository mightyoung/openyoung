---
name: gitnexus-cli
description: "Use when the user needs to run GitNexus CLI commands like analyze/index a repo, check status, clean the index, generate a wiki, or list indexed repos. Examples: 'Index this repo', 'Reanalyze', '索引'"
trigger_patterns:
  - "索引"
  - "index"
  - "analyze"
  - "wiki"
  - "re-index"
tags:
  - cli
  - gitnexus-commands
requires:
  bins:
    - node
    - npm
    - npx
    - gitnexus
---

# GitNexus CLI Operations

## ⚠️ Pre-Check: Environment Setup

### Step 1: Environment Check

```bash
which gitnexus || npx -y gitnexus@latest --version
npm install -g gitnexus  # If not installed
```

## When to Use

- "Index this repo"
- "Reanalyze the codebase"
- "Generate a wiki"
- "Check index status"
- "Clean the index"
- "List indexed repos"

## Available Commands

### Index/Analysis

```bash
# Standard indexing (full)
npx gitnexus analyze

# Force full re-index
npx gitnexus analyze --force

# Skip embeddings (faster)
npx gitnexus analyze --skip-embeddings
```

### Status & Info

```bash
# List all indexed repositories
npx gitnexus list

# Show index status for current repo
npx gitnexus status
```

### Maintenance

```bash
# Delete index for current repo
npx gitnexus clean

# Delete all indexes
npx gitnexus clean --all --force
```

### Wiki Generation

```bash
# Generate repository wiki
npx gitnexus wiki

# With custom model
npx gitnexus wiki --model gpt-4o

# With custom API base URL
npx gitnexus wiki --base-url https://api.anthropic.com/v1

# Force full regeneration
npx gitnexus wiki --force
```

### MCP Server

```bash
# Start MCP server (stdio)
npx gitnexus mcp

# Start local HTTP server (multi-repo)
npx gitnexus serve
```

### Setup

```bash
# Auto-configure MCP for editors
npx gitnexus setup
```

## Workflow Examples

### First Time Setup

```
1. npm install -g gitnexus
2. cd your-project
3. npx gitnexus analyze
4. npx gitnexus setup  # Optional: configure MCP
```

### Update Index After Changes

```
1. git status --porcelain  # Check for changes
2. npx gitnexus analyze --skip-embeddings  # Quick update
3. npx gitnexus status  # Verify
```

### Full Re-index

```
1. npx gitnexus analyze --force
2. Wait for completion
3. Verify: npx gitnexus status
```

## Checklist

```
- [ ] Check if gitnexus is installed
- [ ] Run appropriate command based on task
- [ ] Verify operation completed successfully
- [ ] Report results to user
```

## Tips

- Use `--skip-embeddings` for faster indexing during development
- Use `--force` only when index is corrupted
- Run `npx gitnexus status` to check if re-indexing is needed
- Index is stored in `.gitnexus/` (gitignored)

---
name: gitnexus-refactoring
description: "Use when the user wants to rename, extract, split, move, or restructure code safely. Examples: 'Rename this function', 'Extract this into a module', 'Refactor this class', '重构', '重命名'"
trigger_patterns:
  - "重构"
  - "refactor"
  - "重命名"
  - "rename"
  - "extract"
tags:
  - refactoring
  - code-restructure
requires:
  bins:
    - node
    - npm
    - npx
    - gitnexus
---

# Refactoring with GitNexus

## ⚠️ Mandatory Pre-Check: Environment & Index Health

**Before using ANY GitNexus tools, you MUST complete this check first!**

### Step 1: Environment Check

```bash
which gitnexus || npx -y gitnexus@latest --version
npm install -g gitnexus  # If not installed
```

### Step 2: Index Health Check

```bash
git status --porcelain
npx gitnexus status
npx gitnexus analyze --skip-embeddings  # If stale
```

## When to Use

- "Rename this function"
- "Extract this into a module"
- "Refactor this class"
- "Move this to a separate file"
- Planning any code restructuring
- "重构这部分代码"

## Workflow

```
1. gitnexus_impact({target: "X", direction: "upstream"})  → Find all callers
2. gitnexus_context({name: "X"})                           → Full dependency view
3. gitnexus_rename({old_name, new_name, dry_run: true})   → Preview changes
4. Review and execute rename
5. gitnexus_detect_changes({scope: "all"})                → Verify changes
```

## Checklist

```
- [ ] Complete Environment & Index Health Check
- [ ] gitnexus_impact to find all external callers
- [ ] gitnexus_context to see full dependency graph
- [ ] gitnexus_rename with dry_run: true
- [ ] Review: graph edits (safe) vs text edits (manual review)
- [ ] Execute rename with dry_run: false
- [ ] Verify with gitnexus_detect_changes
```

## Safe Rename Flow

### Step 1: Analyze Impact

```
gitnexus_impact({target: "validateUser", direction: "upstream"})
→ 15 callers found at d=1
→ HIGH risk - need careful planning
```

### Step 2: Dry Run

```
gitnexus_rename({
  symbol_name: "validateUser",
  new_name: "verifyUser",
  dry_run: true
})

→ Files affected: 8
→ Graph edits: 6 (safe - graph understands call graph)
→ Text edits: 2 (manual review needed)
→ Confidence: high
```

### Step 3: Execute

```
# After manual review of text edits
gitnexus_rename({
  symbol_name: "validateUser",
  new_name: "verifyUser",
  dry_run: false
})

→ Renamed successfully
→ All references updated
```

## Extracting/Splitting

When moving code to a new file:

```
1. gitnexus_context({name: "targetFunction"})
   → Incoming: [list of callers]
   → Outgoing: [list of callees]

2. gitnexus_impact({target: "targetFunction", direction: "upstream"})
   → All callers that need updating

3. Plan the move:
   - Update all d=1 callers to import from new location
   - Update internal references

4. gitnexus_detect_changes({scope: "all"})
   → Verify only expected files changed
```

## Runtime Self-Healing

If any tool returns "staleness" warning:

```
1. STOP current operation
2. Run: npx gitnexus analyze --skip-embeddings
3. Re-execute original tool call
4. Verify results are correct before proceeding
```

## ⚠️ CRITICAL Rules

- **NEVER** use find-and-replace for renaming — use `gitnexus_rename`
- **ALWAYS** run dry_run first
- **ALWAYS** manually review text_search_edits
- **MUST** update all d=1 callers before considering done

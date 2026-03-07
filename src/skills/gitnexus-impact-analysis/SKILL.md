---
name: gitnexus-impact-analysis
description: "Use when the user wants to know what will break if they change something, or needs safety analysis before editing code. Examples: 'Is it safe to change X?', 'What depends on this?', 'What will break?', '影响分析', '依赖'"
trigger_patterns:
  - "影响分析"
  - "依赖关系"
  - "impact"
  - "blast radius"
  - "what depends"
tags:
  - impact-analysis
  - dependencies
requires:
  bins:
    - node
    - npm
    - npx
    - gitnexus
---

# Impact Analysis with GitNexus

# Impact Analysis with GitNexus

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

# If stale or missing
npx gitnexus analyze --skip-embeddings
```

## When to Use

- "Is it safe to change this function?"
- "What will break if I modify X?"
- "Show me the blast radius"
- "Who uses this code?"
- Before making non-trivial code changes
- Before committing — to understand what your changes affect

## Workflow

```
1. gitnexus_impact({target: "X", direction: "upstream"})  → What depends on this
2. READ gitnexus://repo/{name}/processes                   → Check affected execution flows
3. gitnexus_detect_changes()                              → Map current git changes to affected flows
4. Assess risk and report to user
```

## Checklist

```
- [ ] Complete Environment & Index Health Check
- [ ] gitnexus_impact({target, direction: "upstream"}) to find dependents
- [ ] Review d=1 items first (these WILL BREAK)
- [ ] Check high-confidence (>0.8) dependencies
- [ ] READ processes to check affected execution flows
- [ ] gitnexus_detect_changes() for pre-commit check
- [ ] Assess risk level and report to user
```

## Understanding Output

| Depth | Risk Level       | Meaning                  |
| ----- | ---------------- | ------------------------ |
| d=1   | **WILL BREAK**  | Direct callers/importers |
| d=2   | LIKELY AFFECTED | Indirect dependencies    |
| d=3   | MAY NEED TESTING| Transitive effects      |

## Risk Assessment

| Affected                       | Risk     |
| ------------------------------ | -------- |
| <5 symbols, few processes      | LOW      |
| 5-15 symbols, 2-5 processes    | MEDIUM   |
| >15 symbols or many processes  | HIGH     |
| Critical path (auth, payments) | CRITICAL |

## Tools

**gitnexus_impact** — the primary tool for symbol blast radius:

```
gitnexus_impact({
  target: "validateUser",
  direction: "upstream",
  minConfidence: 0.8,
  maxDepth: 3
})

→ d=1 (WILL BREAK):
  - loginHandler (src/auth/login.ts:42) [CALLS, 100%]
  - apiMiddleware (src/api/middleware.ts:15) [CALLS, 100%]

→ d=2 (LIKELY AFFECTED):
  - authRouter (src/routes/auth.ts:22) [CALLS, 95%]
```

**gitnexus_detect_changes** — git-diff based impact analysis:

```
gitnexus_detect_changes({scope: "staged"})

→ Changed: 5 symbols in 3 files
→ Affected: LoginFlow, TokenRefresh, APIMiddlewarePipeline
→ Risk: MEDIUM
```

## Example: "What breaks if I change validateUser?"

```
1. gitnexus_impact({target: "validateUser", direction: "upstream"})
   → d=1: loginHandler, apiMiddleware (WILL BREAK)
   → d=2: authRouter, sessionManager (LIKELY AFFECTED)

2. READ gitnexus://repo/my-app/processes
   → LoginFlow and TokenRefresh touch validateUser

3. Risk: 2 direct callers, 2 processes = MEDIUM
```

## Runtime Self-Healing

If any tool returns "staleness" warning:

```
1. STOP current operation
2. Run: npx gitnexus analyze --skip-embeddings
3. Re-execute original tool call
4. Verify results are correct before proceeding
```

## ⚠️ CRITICAL: Never Edit Without Impact Analysis

- **MUST** run `gitnexus_impact` before any modification
- **MUST** warn user if HIGH or CRITICAL risk
- **MUST** update all d=1 (WILL BREAK) dependents

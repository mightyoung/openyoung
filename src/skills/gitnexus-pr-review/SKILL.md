---
name: gitnexus-pr-review
description: "Use when the user wants to review a pull request, understand what a PR changes, assess risk of merging, or check for missing test coverage. Examples: 'Review this PR', 'Is this PR safe to merge?', 'PR审查'"
trigger_patterns:
  - "PR"
  - "review"
  - "合并"
  - "pull request"
  - "审查"
tags:
  - pr-review
  - code-review
requires:
  bins:
    - node
    - npm
    - npx
    - gitnexus
---

# PR Review with GitNexus

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

- "Review this PR"
- "What does PR #42 change?"
- "Is this PR safe to merge?"
- "Check for missing test coverage"
- "评估这个PR的风险"

## Workflow

```
1. git diff --name-only                              → List changed files
2. gitnexus_detect_changes({scope: "staged"})      → Changed symbols
3. For each high-risk symbol:
   - gitnexus_impact({target, direction: "upstream"})
4. Assess overall risk
5. Report findings
```

## Checklist

```
- [ ] Complete Environment & Index Health Check
- [ ] git diff to see changed files
- [ ] gitnexus_detect_changes to see affected symbols
- [ ] For each changed symbol:
    - [ ] gitnexus_impact to assess blast radius
    - [ ] Check if tests exist
- [ ] Identify HIGH/CRITICAL risk areas
- [ ] Report merge recommendation
```

## Risk Assessment for PR

| Impact Area                  | Risk     | Action Required                        |
| ---------------------------- | -------- | -------------------------------------- |
| Core business logic changed | CRITICAL | Deep review, extensive testing         |
| API signature changed        | HIGH     | Update all callers, version bump       |
| Internal refactor           | MEDIUM   | Verify no breaking changes              |
| Tests only                  | LOW      | Quick approval                         |
| Documentation only           | LOW      | Quick approval                         |

## Tools

**gitnexus_detect_changes** — analyze PR scope:

```
gitnexus_detect_changes({scope: "staged"})

→ Changed files: 5
→ Changed symbols: 12
→ Affected: LoginFlow, UserService
→ Risk: MEDIUM
```

**gitnexus_impact** — blast radius per symbol:

```
For each changed symbol:
  gitnexus_impact({target, direction: "upstream"})
  → d=1 callers that will be affected
```

## Example: "Review PR #42"

```
1. git diff --name-only origin/main...HEAD
   → src/auth/login.ts, src/api/user.ts, tests/auth.test.ts

2. gitnexus_detect_changes({scope: "compare", base_ref: "main"})
   → Changed: validateToken, createSession
   → Affected: LoginFlow, OAuthFlow

3. gitnexus_impact({target: "validateToken", direction: "upstream"})
   → 8 callers at d=1
   → HIGH risk

4. Summary:
   - 2 core functions changed
   - 8 dependent functions affected
   - Test coverage exists
   - Recommendation: Review carefully, run full test suite
```

## Runtime Self-Healing

If any tool returns "staleness" warning:

```
1. STOP current operation
2. Run: npx gitnexus analyze --skip-embeddings
3. Re-execute original tool call
4. Verify results are correct before proceeding
```

## Output Template

```
## PR Review Summary

### Changed Files
| File | Change Type |
|------|-------------|
| src/auth/login.ts | Modified |

### Impact Analysis
| Symbol | Risk | Callers |
|--------|------|---------|
| validateToken | HIGH | 8 |

### Test Coverage
- ✓ Tests exist for changed logic

### Recommendation
[APPROVE / NEEDS_CHANGES / CRITICAL]

### Notes
[Additional observations]
```

---
name: gitnexus-exploring
description: "Use when the user asks how code works, wants to understand architecture, trace execution flows, or explore unfamiliar parts of the codebase. Examples: 'How does X work?', 'What calls this function?', 'Show me the auth flow', '代码结构', '架构分析'"
trigger_patterns:
  - "代码结构"
  - "架构分析"
  - "理解代码"
  - "explore"
  - "understand code"
tags:
  - code-analysis
  - knowledge-graph
requires:
  bins:
    - node
    - npm
    - npx
    - gitnexus
---

# Code Exploring with GitNexus

## ⚠️ Mandatory Pre-Check: Environment & Index Health

**Before using ANY GitNexus tools, you MUST complete this check first!**

### Step 1: Environment Check

```bash
# Check if gitnexus is installed
which gitnexus || npx -y gitnexus@latest --version

# If not installed, install it
npm install -g gitnexus
```

### Step 2: Index Health Check

```bash
# Check git status
git status --porcelain

# Check index status
npx gitnexus status

# If stale or missing, re-index
npx gitnexus analyze --skip-embeddings
```

### Auto-Detection Logic

```
IF gitnexus not installed:
    → npm install -g gitnexus
    → Continue

ELSE IF index not exist:
    → npx gitnexus analyze
    → Continue

ELSE IF git commits behind HEAD:
    → npx gitnexus analyze --skip-embeddings
    → Continue

ELSE:
    → Continue to analysis
```

## When to Use

- "How does authentication work?"
- "What's the project structure?"
- "Show me the main components"
- "Where is the database logic?"
- Understanding code you haven't seen before
- "代码架构是怎么样的"

## Workflow

```
1. READ gitnexus://repos                              → Discover indexed repos
2. READ gitnexus://repo/{name}/context               → Codebase overview, check staleness
3. gitnexus_query({query: "<what you want to understand>"})  → Find related execution flows
4. gitnexus_context({name: "<symbol>"})              → Deep dive on specific symbol
5. READ gitnexus://repo/{name}/process/{name}        → Trace full execution flow
```

## Checklist

```
- [ ] Complete Environment & Index Health Check
- [ ] READ gitnexus://repo/{name}/context
- [ ] gitnexus_query for the concept you want to understand
- [ ] Review returned processes (execution flows)
- [ ] gitnexus_context on key symbols for callers/callees
- [ ] READ process resource for full execution traces
- [ ] Read source files for implementation details
```

## Tools

**gitnexus_query** — find execution flows related to a concept:

```
gitnexus_query({query: "payment processing"})
→ Processes: CheckoutFlow, RefundFlow, WebhookHandler
→ Symbols grouped by flow with file locations
```

**gitnexus_context** — 360-degree view of a symbol:

```
gitnexus_context({name: "validateUser"})
→ Incoming calls: loginHandler, apiMiddleware
→ Outgoing calls: checkToken, getUserById
→ Processes: LoginFlow (step 2/5), TokenRefresh (step 1/3)
```

## Resources

| Resource                                | What you get                                            |
| --------------------------------------- | ------------------------------------------------------- |
| `gitnexus://repo/{name}/context`        | Stats, staleness warning (~150 tokens)                  |
| `gitnexus://repo/{name}/clusters`       | All functional areas with cohesion scores (~300 tokens) |
| `gitnexus://repo/{name}/cluster/{name}`| Area members with file paths (~500 tokens)              |
| `gitnexus://repo/{name}/process/{name}`| Step-by-step execution trace (~200 tokens)              |

## Example: "How does payment processing work?"

```
1. READ gitnexus://repo/my-app/context       → 918 symbols, 45 processes
2. gitnexus_query({query: "payment processing"})
   → CheckoutFlow: processPayment → validateCard → chargeStripe
   → RefundFlow: initiateRefund → calculateRefund → processRefund
3. gitnexus_context({name: "processPayment"})
   → Incoming: checkoutHandler, webhookHandler
   → Outgoing: validateCard, chargeStripe, saveTransaction
4. Read src/payments/processor.ts for implementation details
```

## Runtime Self-Healing

If any tool returns "staleness" warning:

```
1. STOP current operation
2. Run: npx gitnexus analyze --skip-embeddings
3. Wait for indexing to complete
4. Re-execute original tool call
5. Verify results are correct before proceeding
```

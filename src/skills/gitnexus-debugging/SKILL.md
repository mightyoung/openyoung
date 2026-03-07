---
name: gitnexus-debugging
description: "Use when the user is debugging a bug, tracing an error, or asking why something fails. Examples: 'Why is X failing?', 'Where does this error come from?', 'Trace this bug', '调试', '找bug'"
trigger_patterns:
  - "调试"
  - "debug"
  - "bug"
  - "trace"
  - "错误"
tags:
  - debugging
  - error-tracing
requires:
  bins:
    - node
    - npm
    - npx
    - gitnexus
---

# Debugging with GitNexus

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

- "Why is this function failing?"
- "Trace where this error comes from"
- "Who calls this method?"
- "This endpoint returns 500"
- Investigating bugs, errors, or unexpected behavior

## Workflow

```
1. gitnexus_query({query: "<error or symptom>"})            → Find related execution flows
2. gitnexus_context({name: "<suspect>"})                    → See callers/callees/processes
3. READ gitnexus://repo/{name}/process/{name}              → Trace execution flow
4. gitnexus_cypher({query: "MATCH path..."})              → Custom traces if needed
```

## Checklist

```
- [ ] Complete Environment & Index Health Check
- [ ] Understand the symptom (error message, unexpected behavior)
- [ ] gitnexus_query for error text or related code
- [ ] Identify the suspect function from returned processes
- [ ] gitnexus_context to see callers and callees
- [ ] Trace execution flow via process resource if applicable
- [ ] gitnexus_cypher for custom call chain traces if needed
- [ ] Read source files to confirm root cause
```

## Debugging Patterns

| Symptom              | GitNexus Approach                                          |
| -------------------- | ---------------------------------------------------------- |
| Error message        | `gitnexus_query` for error text → `context` on throw sites |
| Wrong return value   | `context` on the function → trace callees for data flow    |
| Intermittent failure | `context` → look for external calls, async deps            |
| Performance issue    | `context` → find symbols with many callers (hot paths)     |
| Recent regression    | `detect_changes` to see what your changes affect           |

## Tools

**gitnexus_query** — find code related to error:

```
gitnexus_query({query: "payment validation error"})
→ Processes: CheckoutFlow, ErrorHandling
→ Symbols: validatePayment, handlePaymentError, PaymentException
```

**gitnexus_context** — full context for a suspect:

```
gitnexus_context({name: "validatePayment"})
→ Incoming calls: processCheckout, webhookHandler
→ Outgoing calls: verifyCard, fetchRates (external API!)
→ Processes: CheckoutFlow (step 3/7)
```

**gitnexus_cypher** — custom call chain traces:

```cypher
MATCH path = (a)-[:CodeRelation {type: 'CALLS'}*1..2]->(b:Function {name: "validatePayment"})
RETURN [n IN nodes(path) | n.name] AS chain
```

## Example: "Payment endpoint returns 500 intermittently"

```
1. gitnexus_query({query: "payment error handling"})
   → Processes: CheckoutFlow, ErrorHandling
   → Symbols: validatePayment, handlePaymentError

2. gitnexus_context({name: "validatePayment"})
   → Outgoing calls: verifyCard, fetchRates (external API!)

3. READ gitnexus://repo/my-app/process/CheckoutFlow
   → Step 3: validatePayment → calls fetchRates (external)

4. Root cause: fetchRates calls external API without proper timeout
```

## Runtime Self-Healing

If any tool returns "staleness" warning:

```
1. STOP current operation
2. Run: npx gitnexus analyze --skip-embeddings
3. Re-execute original tool call
4. Verify results are correct before proceeding
```

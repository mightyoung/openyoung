# OpenYoung Security Threat Model

> This document describes the security architecture, threat model, and isolation capabilities of OpenYoung's AI Sandbox system.

## Architecture Overview

OpenYoung's AI Sandbox uses a **multi-backend architecture** to provide secure code execution:

```
┌─────────────────────────────────────────────────────────────┐
│                     SandboxManager                          │
│  (SecurityPolicyEngine + Risk Assessment + Audit Logging)  │
└─────────────────┬───────────────────────┬─────────────────┘
                  │                       │                   │
                  ▼                       ▼                   ▼
           ┌────────────┐          ┌────────────┐     ┌────────────┐
           │    E2B     │          │   Docker   │     │  Process   │
           │ (microVM)  │          │  (future)  │     │(subprocess)│
           │            │          │            │     │            │
           │  RECOMMENDED │         │ NOT YET    │     │ FALLBACK   │
           └────────────┘          └────────────┘     └────────────┘
```

## Backend Comparison

| Feature | E2B (microVM) | Docker | Process (subprocess) |
|---------|---------------|--------|---------------------|
| **Isolation Level** | microVM | container | OS process |
| **Network Isolation** | native | native | host network |
| **Filesystem Isolation** | isolated | isolated | host filesystem |
| **Resource Limits** | full | full | timeout only |
| **Path Traversal Protection** | yes | yes | **no** |
| **Working Directory Restriction** | yes | yes | **no** |
| **Status** | Available | Not implemented | **Default/Fallback** |

## Security Controls by Backend

### E2B Backend (Recommended)

E2B provides **microVM-level isolation** with:
- Full network isolation (no host network access)
- Filesystem isolation (temporary filesystem)
- Resource limits (CPU, memory, time)
- Built-in sandbox escape detection
- Native execution environment

**Use E2B for production workloads requiring strong security guarantees.**

### Docker Backend (Not Yet Implemented)

Docker backend is planned but not yet implemented. When completed, it will provide:
- Container-based isolation
- Network namespace isolation
- Filesystem overlay
- Resource limits via cgroups

### Process Backend (Fallback - Current Default)

The **subprocess-based sandbox** is the current default and provides **limited security**:

#### Implemented Security Controls

1. **Timeout Protection**
   - Execution time limit via `subprocess.run(timeout=...)`
   - Prevents indefinite execution

2. **Network Command Blocking**
   - Detects and blocks commands: `curl`, `wget`, `nc`, `netcat`, `ssh`, `scp`, `rsync`, `telnet`, `ftp`, `sftp`
   - Only when `allow_network=False` in policy

3. **Risk Assessment**
   - Code scanned for dangerous patterns before execution
   - Blocked patterns include: `rm -rf`, `dd if=`, `import os.*system`, `subprocess.*shell\s*=\s*True`, `eval(`, `exec(`, `__import__('os')`, `import pty`, `import socket`

4. **Prompt Injection Detection**
   - Detects malicious prompt patterns

5. **Secret Scanning**
   - Detects exposed API keys, passwords, tokens

#### NOT Implemented (Process Backend)

The Process backend does **NOT** provide:

| Missing Control | Risk | Mitigation |
|----------------|------|------------|
| **Filesystem isolation** | Code can access any host file | Use E2B for sensitive workloads |
| **Path traversal prevention** | `../../etc/passwd` attacks possible | Use E2B for sensitive workloads |
| **Working directory restriction** | No chroot-like restriction | Use E2B for sensitive workloads |
| **CPU/Memory limits** | No `resource.setrlimit()` | Use E2B for sensitive workloads |
| **True network isolation** | Process uses host network | Use E2B for sensitive workloads |
| **Environment variable filtering** | Full host env accessible | Use E2B for sensitive workloads |

## Threat Model

### Assets to Protect

1. **Host Filesystem** - Confidential files, credentials, SSH keys
2. **Network** - Internal services, APIs, databases
3. **Process Resources** - CPU, memory, file descriptors
4. **Environment Variables** - API keys, tokens, paths

### Threats and Mitigations

| Threat | Process Backend | E2B Backend |
|--------|----------------|-------------|
| Malicious code execution | Partial (timeout + pattern block) | Full mitigation |
| Filesystem access | **NOT PROTECTED** | Protected |
| Path traversal attack | **NOT PROTECTED** | Protected |
| Network exfiltration | **NOT PROTECTED** | Protected |
| Resource exhaustion | Timeout only | Full limits |
| Sandbox escape | **NOT PROTECTED** | Protected |
| Credential theft | **NOT PROTECTED** | Protected |

### Risk Assessment

**HIGH RISK**: Running untrusted code with Process backend because:
- No filesystem isolation
- No path traversal protection
- No true network isolation
- No resource limits beyond timeout

**RECOMMENDATION**: For untrusted code, always use E2B backend.

## Usage Recommendations

### Development/Testing

Process backend is acceptable for:
- Running trusted agent code
- Quick experimentation
- Local development

```python
config = SandboxConfig(
    backend=SandboxBackend.PROCESS,
    policy=SandboxPolicy(allow_network=False)
)
```

### Production

**Always use E2B backend for production:**

```python
config = SandboxConfig(
    backend=SandboxBackend.E2B,
    policy=SandboxPolicy(allow_network=False)
)
```

### Security-Critical Workloads

For security-critical workloads:
1. Use E2B backend exclusively
2. Enable all security features in policy
3. Enable audit logging
4. Use network whitelist when network is needed

## Security Policy Configuration

```python
from src.runtime.sandbox.security_policy import SandboxPolicy, RiskLevel

# Strict policy for untrusted code
policy = SandboxPolicy(
    force_sandbox=True,
    min_risk_level=RiskLevel.LOW,
    allow_network=False,
    enable_audit=True,
    enable_escape_detection=True,
    block_path_traversal=True,
)
```

## Audit and Monitoring

Enable audit logging to track:

```python
policy = SandboxPolicy(
    enable_audit=True,
    audit_level="info"  # debug, info, warning, error
)
```

Audit events include:
- Code execution requests
- Risk assessments
- Blocked operations
- Network access attempts
- Execution outcomes

## References

- E2B Security: https://e2b.dev/docs/security
- Sandbox Security Best Practices: https://docs.e2b.dev/docs/security
- NIST Container Security Guide

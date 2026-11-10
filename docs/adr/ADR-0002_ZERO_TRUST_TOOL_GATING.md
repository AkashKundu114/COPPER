# ADR-0002: Zero-Trust Tool Gating & Least-Privilege Execution

## Status
**Accepted**

## Context
Autonomous agents within COPPER execute system utilities, run shell scripts, query databases, and read/write local files. Naive agent execution models trust agent-generated tool calls implicitly, exposing workstations to prompt injection, privilege escalation, and accidental data destruction.

## Decision
1. **Never Trust Agent Directives**: No tool call is executed based merely on LLM intent.
2. **Two-Factor Gating**:
   - **Zero-Trust Authorization**: `ToolAuthorizationPolicy` verifies caller permissions and cryptographic agent token scopes before execution.
   - **Guardian Safety Evaluation**: `GuardianEngine` checks for destructive commands, adversarial text normalization, dynamic friction thresholds, and memory provenance authority.
3. **Four-Tier Action Classification**: All actions are classified as `READ_ONLY`, `REVERSIBLE`, `CONSEQUENTIAL`, or `IRREVERSIBLE`. `CONSEQUENTIAL` actions require explicit operator confirmation tickets. `IRREVERSIBLE` actions are unconditionally blocked.

## Consequences
- **Positive**: Eliminates remote code execution via prompt injection, enforces least privilege, and guarantees human approval for high-impact workstation modifications.
- **Negative**: Adds sub-millisecond evaluation latency (<20 µs) and requires operator confirmation for consequential actions.

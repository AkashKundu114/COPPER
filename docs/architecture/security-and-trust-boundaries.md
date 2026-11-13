# Security Architecture and Trust Boundaries

C.O.P.P.E.R. operates under an uncompromising **Zero-Trust Security Architecture**. No component—whether an internal subagent, background worker, external tool, or memory provider—is inherently trusted.

---

## 1. Architectural Trust Boundaries

```
[ UNTRUSTED INTERFACE: Web Content, User Ingest, External Files, Tool Outputs ]
                                  |
                                  v
+=============================================================================+
| TRUST BOUNDARY 1: Input Normalization & Injection Defense                   |
| - normalize_adversarial_text (homoglyphs, invisible zero-width chars)       |
| - sanitize_untrusted_text (control-plane tag escaping)                      |
| - scan_for_indirect_injection (re-routing, prompt injection triggers)       |
+=============================================================================+
                                  |
                                  v
+=============================================================================+
| TRUST BOUNDARY 2: Policy & Safety Gating                                    |
| - ArchitecturalControlPlane.evaluate_policy()                               |
| - DynamicTrustFabricEvaluator (subagent behavioral scoring & tier demotion) |
| - Guardian Safety Engine (hard safety invariants)                           |
| - 4-Tier Action Classifier (Read-only, Reversible, Consequential, Blocked)  |
+=============================================================================+
                                  |
                                  v
+=============================================================================+
| TRUST BOUNDARY 3: Tool & Subprocess Execution Sandboxing                    |
| - AgentToken capability scoping (HMAC-signed allowed tools whitelist)       |
| - Forge Sandbox (isolated temporary working directories)                    |
| - AST command validator (rejection of fork bombs, PTY escapes, rm -rf)      |
+=============================================================================+
                                  |
                                  v
+=============================================================================+
| TRUST BOUNDARY 4: Privacy & Secondary Store Isolation                       |
| - DataFirewall application-layer PII and secret redaction                   |
| - Multi-store verifiable deletion (SQLite, ChromaDB, Redis)                 |
| - Cryptographic HMAC-SHA256 audit chaining & WORM vault retention           |
+=============================================================================+
```

---

## 2. Hard Security Invariants

1. **Local-First Zero Egress (`SEC-001`):**
   Runtime operations are bound to loopback interfaces (`127.0.0.1`, `localhost`). Outbound external network connections are denied by default unless an explicit, operator-confirmed network egress policy is granted for a specific tool.
2. **Subagent Least Privilege:**
   Subagents (e.g. `AXIS`, `OMNI`, `FORGE`) do not receive raw shell or OS access. Each subagent is issued an `AgentToken` with a whitelisted set of allowed tools. Tool requests outside this token are rejected.
3. **No Unaudited State Changes:**
   Every tool execution, privilege escalation, or configuration modification is notarized into the cryptographic audit chain.
4. **Secret Protection Invariant:**
   Private keys, API tokens, and user credentials stored in `SecretVault` are encrypted using AES-GCM and never leaked through diagnostics, exception tracebacks, or telemetry logs.

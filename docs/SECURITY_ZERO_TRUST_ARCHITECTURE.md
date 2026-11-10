# C.O.P.P.E.R. Zero-Trust Security Architecture

**Version:** 1.0.0  
**Classification:** Core System Architecture  
**Target Specification:** Zero-Trust Computing Architecture for Local-First AI Operating Systems  
**Audited Subsystems:** `GuardianEngine`, `DataFirewall`, `ForgeSandbox`, `ASTValidator`, `ToolExecutor`, `NetworkMode`, `BaseAgent`, `FastAPI Middleware`

---

## 1. Architectural Philosophy & Zero-Trust Core Tenets

Traditional AI agent frameworks treat agents and internal orchestration pipelines as implicit trusted zones. C.O.P.P.E.R. rejects perimeter-only trust and implements a **Formal Zero-Trust Architecture (ZTA)** governed by eight foundational axioms:

1. **Explicit Identity Verification:** Never trust an agent, tool, or API request merely because it originates within the host environment.
2. **Least Privilege Execution:** Every agent operates within a strictly defined, cryptographically signed capability boundary (`AgentToken`).
3. **Execution-Time Authorization:** Every tool invocation is authorized at the `ToolExecutor` boundary regardless of prior routing decisions.
4. **Untrusted Data Isolation:** All external inputs—including web search results, scraped pages, retrieved files, and multi-agent observations—are classified as untrusted and neutralized before reaching the LLM control plane.
5. **Dual-Plane Memory Governance:** Retrieval from epistemic memory does not confer execution authority ($\text{Authority} = \gamma(m) \times \mathcal{C}(m) \times (1 - \mathcal{R}(a))$).
6. **Network Containment Outside LLM Control:** Network egress policies (`OFFLINE_AIRGAP`, `LOCAL_SERVICES`, `USER_AUTHORIZED_EGRESS`) and SSRF defenses are enforced deterministically at the socket and protocol layer, completely inaccessible to prompt manipulation.
7. **Secret & Credential Segregation:** Secrets are stored in an in-memory vault and dynamically registered with the `DataFirewall` regex filter, preventing exposure through prompts, logs, or memory.
8. **Continuous Adaptive Friction:** Cognitive fatigue ($\text{DFM-Guard}$) and reversibility risk continuously calibrate confirmation thresholds.

---

## 2. Zero-Trust Subsystem Map

```
                                      ┌─────────────────────────────────────────────────────────┐
                                      │              EXTERNAL & USER BOUNDARY                   │
                                      │   [FastAPI] Bearer Token / X-API-Key / Rate Limiting    │
                                      └────────────────────────────┬────────────────────────────┘
                                                                   │
                                                                   ▼
                                      ┌─────────────────────────────────────────────────────────┐
                                      │              AUTHENTICATION & RBAC/ABAC                 │
                                      │   Principal Resolution: KeyManager & AccessController   │
                                      └────────────────────────────┬────────────────────────────┘
                                                                   │
                                                                   ▼
                                      ┌─────────────────────────────────────────────────────────┐
                                      │                 AGENT CONTROL PLANE                     │
                                      │   BaseAgent: Cryptographic AgentToken (HMAC-SHA256)     │
                                      │   PromptInjectionGuard: Neutralize & Escaped Context    │
                                      └────────────────────────────┬────────────────────────────┘
                                                                   │
                                                                   ▼
                                      ┌─────────────────────────────────────────────────────────┐
                                      │                TOOL AUTHORIZATION GATE                  │
                                      │   ToolExecutor + ToolAuthorizationPolicy                │
                                      │   GuardianEngine (Friction, Fatigue, MemoryQuarantine)  │
                                      └───────┬────────────────────┬────────────────────┬───────┘
                                              │                    │                    │
                      ┌───────────────────────┴──────┐             │                    └───────────────────────┐
                      ▼                              ▼             ▼                                            ▼
          ┌───────────────────────┐      ┌───────────────────────────────┐                  ┌───────────────────────────────┐
          │     FORGE SANDBOX     │      │         NETWORK POLICY        │                  │          SECRET VAULT         │
          │ Docker / Pyodide WASM │      │ SSRF Defense & RFC 1918 Block │                  │ In-Memory Key Segregation     │
          │ Kernel Job Objects    │      │ NetworkMode Enclosure         │                  │ Dynamic DataFirewall Masking  │
          │ AST Security Traversal│      └───────────────────────────────┘                  └───────────────────────────────┘
          └───────────────────────┘
```

---

## 3. Subsystem Detailed Specifications

### 3.1 Authentication & Principal Identity Management (`app.core.security.auth`)
- **Key Manager (`KeyManager`):** Generates a 256-bit entropy host operator key stored at `data/copper_operator.key` with restricted access permissions (`0600` on POSIX).
- **Constant-Time Verification:** Uses `hmac.compare_digest` to prevent timing attacks.
- **Dual Scheme:** Supports `X-API-Key: <key>` and `Authorization: Bearer <token>`.
- **Principal Abstraction:** Yields an authenticated `Principal` object tracking identity, principal type (`OPERATOR`, `AGENT`, `SYSTEM`, `ANONYMOUS`), granted role, and scoped capabilities.

### 3.2 Role-Based & Attribute-Based Access Control (`app.core.security.access_control`)
- **Role Hierarchy:**
  - `ADMIN`: Full operational and policy control.
  - `OPERATOR`: Interactive task execution, agent activation, safe and moderate tool execution.
  - `AGENT`: Restricted autonomy scoped strictly to assigned agent purpose.
  - `AUDITOR`: Read-only telemetry, audit log review, and data export.
  - `READ_ONLY`: Public dashboard and system status inspection.
- **ABAC Context Evaluation (`ABACContext`):**
  - High-impact data destruction (`audit:delete`) requires `ADMIN` role **plus** explicit operator confirmation.
  - Tool execution in `OFFLINE_AIRGAP` automatically revokes external network permissions.
  - Critical tool execution (`shell_execute`) requires explicit operator confirmation.

### 3.3 Cryptographic Agent Identity & Capability Tokens (`app.core.security.agent_token`)
- **Agent Tokens (`agtok.<payload>.<sig>`):**
  - Issued per agent turn with finite validity ($TTL = 300\text{s}$).
  - Cryptographically bound to the agent type and allowed tool list.
  - Tamper-evident: Signed with HMAC-SHA256 using the host operator key.
  - Verified at the `ToolExecutor` boundary before executing any tool function.

### 3.4 Tool-Level Permission Enforcement (`app.core.security.tool_policy`)
- Gated in `ToolExecutor.execute()`:
  - If invoked by an agent, verifies that the target tool is explicitly present in the agent's verified token.
  - If invoked by an API principal, evaluates RBAC matrix against tool guardian level ($L0 \implies \text{Safe}, L1 \implies \text{Moderate}, L2 \implies \text{Sensitive}, L3 \implies \text{Critical}$).
  - Prevents cross-agent lateral movement (e.g. an image or reminder agent invoking shell execution).

### 3.5 Indirect Prompt Injection Defense (`app.core.security.prompt_injection`)
- **Tag Sanitization:** External inputs and tool results are scanned for control tags (`<tool_call>`, `</tool_call>`, `<tool_result>`, `<system>`) and sanitized before injection into the prompt stream.
- **Provenance Forgery Neutralization:** Intercepts fake `[MEMORY provenance=user_explicit ...]` markers embedded in external documents and demotes them to `provenance=external_untrusted`.
- **Heuristic Scanning:** Scans for indirect instruction hijacking phrases (`"ignore previous instructions"`, `"disregard safety rules"`).

### 3.6 Network Egress & SSRF Protection (`app.core.security.network_policy`)
- **Enforced Outside LLM Control:**
  - Blocks AWS/GCP/Azure link-local metadata endpoints (`169.254.169.254`, `metadata.google.internal`).
  - Resolves target hostnames prior to connection and blocks private RFC 1918 subnets (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`) in WAN egress mode.
  - `LOCAL_SERVICES` mode confines network calls exclusively to local loopback (`127.0.0.1`, `localhost`).
  - `OFFLINE_AIRGAP` mode prohibits all socket egress immediately.

### 3.7 Secret & Credential Vault (`app.core.security.secret_vault`)
- **In-Memory Segregation:** Credentials and API keys are stored in an isolated vault in memory.
- **Dynamic Firewall Synchronization:** Storing a secret automatically injects its literal value into `DataFirewall._PATTERNS`, guaranteeing that any attempt to echo or serialize the secret into logs, vector memories, or chat history is masked as `•••VAULT_SECRET_REDACTED•••`.

### 3.8 API Abuse Prevention & Rate Limiting (`app.core.security.rate_limiter`)
- **Sliding-Window Limiter:** Tracks requests in sliding 10-second and 60-second windows per client IP.
- **Tiered Quotas:** Standard endpoints allow 120 req/min (35 burst/10s); sensitive endpoints allow 20 req/min.
- Emits standard `429 Too Many Requests` with `Retry-After` header upon violation.

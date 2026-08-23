# Security Policy

## Security Overview & Threat Model

**C.O.P.P.E.R.** is engineered with a **local-first, zero-cloud-egress** security model. All AI models, vector embeddings, episodic memories, and execution sandboxes reside strictly within the user's host environment.

---

## Supported Versions

We provide security updates and patches for the following versions:

| Version | Supported | Notes |
| :--- | :---: | :--- |
| **`1.0.x`** | Yes | **Active Support (Current Release)** |
| `< 1.0.0` | No | Deprecated pre-release builds |

---

## Reporting a Vulnerability

We take the security of C.O.P.P.E.R. seriously. If you discover a security vulnerability or bypass in the **Guardian Safety Engine**, **Data Firewall**, or **Forge Code Sandbox**, please follow this responsible disclosure procedure:

1. **Do NOT open a public GitHub Issue.**
2. Send a detailed report to the maintainer:
   - **Email:** `security@copper-ai.local` (or create a private GitHub Security Advisory)
   - **Subject:** `[SECURITY VULNERABILITY] <Component Name>: <Brief Description>`
3. **Include the following information in your report:**
   - Detailed description of the vulnerability and attack vector.
   - Exact steps or proof-of-concept (PoC) script to reproduce the issue.
   - Potential impact (e.g., sandbox escape, PII leakage, Guardian override).
   - Any proposed remediation or mitigation.

### Response Timelines
- **Initial Acknowledgment:** Within **24 hours**.
- **Assessment & Triage:** Within **48 hours**.
- **Fix & Patch Release:** Within **7 business days** for high-severity issues.

---

## Core Security Mechanisms

### 1. Zero-Trust Data Firewall
- Every inbound and outbound prompt is inspected by the regex-based `DataFirewall` prior to LLM inference or persistence.
- Automatic masking of OpenAI tokens (`sk-`, `sk-proj-`), JWT Bearer tokens, SSNs, credit card numbers, personal file paths, and private IP addresses.

### 2. Multi-Level Guardian Alignment Engine
- **Level 0 (Execute):** Safe, non-destructive read operations execute immediately.
- **Level 1 (Suggest):** Performance optimizations and non-blocking advice.
- **Level 2 (Challenge):** Personal commitment conflicts and focus overrides require explicit user acknowledgment.
- **Level 3 (Safety Boundary):** Irreversible destructive operations (`rm -rf`, drive formats, database drops) require case-sensitive `"confirm"` validation.

### 3. Forge Code Execution Sandbox
- Isolated sub-process execution for coding agent scripts with strict execution timeouts (10s default, configurable), separate working directories, and automated temporary script cleanup.

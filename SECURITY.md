# Security Policy

## Security Overview & Threat Model

**C.O.P.P.E.R.** (Centralized Omnifunctional Personal Productivity and Execution Routine) is engineered with a **local-first, zero-cloud-egress** architecture created and maintained by **Akash Kundu**.

All AI models, vector embeddings, episodic memories, and execution sandboxes reside strictly within the user's host environment. No prompt data, audio recordings, telemetry, or personal facts leave your machine without your explicit affirmative action.

---

## Supported Versions

We provide active security updates, vulnerability fixes, and patches for the following versions:

| Version | Supported | Status |
| :--- | :---: | :--- |
| **`1.1.x`** | **Yes** | **Current Active Release** |
| **`1.0.x`** | **Yes** | **Maintenance Support** |
| `< 1.0.0` | No | Deprecated Pre-Release Builds |

---

## Reporting a Vulnerability

We take the security and privacy of C.O.P.P.E.R. extremely seriously. If you discover a security vulnerability, sandbox escape, Data Firewall PII leak, or Guardian safety bypass, please report it through our responsible disclosure channels.

### Responsible Disclosure Protocol:

1. **Do NOT file a public GitHub Issue** for security vulnerabilities.
2. Submit your report privately to the maintainer:
   - **Maintainer:** Akash Kundu
   - **Email:** `security@copper-ai.local`
   - **GitHub Security Advisory:** [Open Private Advisory](https://github.com/AkashKundu114/COPPER/security/advisories/new)
   - **Subject Line:** `[SECURITY VULNERABILITY] <Component Name>: <Brief Summary>`
3. **Include the following information in your report:**
   - Detailed description of the vulnerability and attack vector.
   - Exact steps or proof-of-concept (PoC) script to reproduce the issue.
   - Affected components (e.g., Data Firewall, Guardian Engine, Forge Sandbox, REST/WebSocket API).
   - Potential impact assessment (e.g., arbitrary code execution, unintended PII exposure, safety boundary override).
   - Any proposed remediation, patch, or mitigation strategy.

### Response Timelines (SLA):
- **Initial Acknowledgment:** Within **24 hours**.
- **Assessment & Triage:** Within **48 hours**.
- **Fix & Patch Release:** Within **7 business days** for high/critical-severity issues.

Please allow sufficient time for verification and patch deployment before any public disclosure.

---

## Core Security Mechanisms

### 1. Zero-Trust Data Firewall (`backend/app/core/data_firewall.py`)
- In-line regular expression and heuristic pattern matcher analyzing all inbound user inputs and outbound agent responses.
- Automatic masking and synthetic tokenization of:
  - OpenAI API tokens (`sk-`, `sk-proj-`) and JWT Bearer authorization headers.
  - Social Security Numbers (SSNs) and Credit Card numbers (Luhn-compliant patterns).
  - Personal email addresses, private IPv4/IPv6 addresses, and sensitive local filesystem paths.

### 2. Multi-Level Guardian Safety & Alignment Engine (`backend/app/core/guardian.py`)
- **Level 0 (Execute):** Safe, non-destructive read operations and routine tasks execute immediately without friction.
- **Level 1 (Suggest):** Contextual advice and non-blocking performance suggestions.
- **Level 2 (Challenge):** Intercepts commitment conflicts, energy fatigue overrides, or high-distraction workflows, requiring explicit user affirmation (`GuardianChallengeModal`).
- **Level 3 (Safety Boundary):** Intercepts destructive system commands (`rm -rf`, disk formatting, database drops, root modifications), requiring mandatory case-sensitive `"confirm"` validation.

### 3. Forge Code Execution Sandbox (`backend/app/core/forge_sandbox.py`)
- Isolated subprocess environment for software engineering agents (AXIS).
- Hard execution timeouts (configurable default 10s).
- Sandboxed working directories preventing arbitrary filesystem writes outside target project scopes.
- Automated cleanup of temporary execution artifacts and sandboxed environment variables.

### 4. Epistemic Vector Persistence & Privacy
- Local SQLite database and ChromaDB vector index (`nomic-embed-text-v1.5`) operate 100% on-device.
- One-click encrypted JSON export and instant, permanent audit log purge (`delete-all`) via the Security Center.


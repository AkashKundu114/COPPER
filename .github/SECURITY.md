# Security Policy & Vulnerability Reporting

**C.O.P.P.E.R.** takes user privacy, zero-trust data firewall protection, and 100% offline execution security seriously.

## Supported Versions

| Version | Supported | Status |
| :--- | :---: | :--- |
| **`1.1.x`** | **Yes** | **Current Active Release** |
| **`1.0.x`** | **Yes** | **Maintenance Support** |
| `< 1.0.0` | No | Deprecated Pre-Release Builds |

## Reporting a Vulnerability

If you discover a security vulnerability (such as a Data Firewall PII leak, Forge sandbox escape, or Guardian safety boundary bypass), please report it privately:

1. **Email:** Send full vulnerability details to **`security@copper-ai.local`** (Maintainer: **Akash Kundu**).
2. **GitHub Security Advisory:** [Open a Private Vulnerability Report](https://github.com/AkashKundu114/COPPER/security/advisories/new).
3. **Details to include:**
   - Proof of Concept (PoC) script or detailed reproduction steps.
   - Affected component (Data Firewall, Guardian Engine, Forge Sandbox, REST API, WebSocket Endpoint).
   - Impact assessment (e.g., arbitrary code execution, unintended PII egress, safety boundary override).
   - Proposed remediation or patch.

## Response Timelines

- **Initial Acknowledgment:** Within **24 hours**.
- **Triage & Severity Assessment:** Within **48 hours**.
- **Patch Release:** High/Critical severity issues patched within **7 business days**.

Please do not disclose security issues publicly until a patch has been released. For complete architectural and threat model details, see [SECURITY.md](../SECURITY.md).


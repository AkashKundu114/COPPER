# C.O.P.P.E.R. Zero-Trust Threat Model & Attack-Surface Inventory

**Target System:** C.O.P.P.E.R. Core Architecture  
**Methodology:** STRIDE Threat Classification & Attacker Modeling ($\mathcal{A}$)  
**Verification Suite:** `tests/security/` (107 automated test cases)

---

## 1. Threat Model & Attacker Capabilities ($\mathcal{A}$)

The adversary $\mathcal{A}$ operates under a grey-to-white box model with the following assumed capabilities and limits:
- **Capabilities:**
  - Can submit arbitrary prompts through the chat interface or local API.
  - Can host malicious web content, RSS feeds, or documents ingested by `web_search`, `web_fetch`, `scrapling_scrape`, or document parsers.
  - Can craft synthetic multi-turn conversations and forge memory metadata tags (`[MEMORY provenance=...]`).
  - Can probe network ports and simulate concurrent request bursts.
- **Constraints:**
  - No physical access to the workstation hardware.
  - No access to modify model weights or operating system kernel binaries.
  - Cannot break standard cryptographic primitives (HMAC-SHA256, SHA-256).

---

## 2. STRIDE Threat Analysis Matrix

| Threat Category | Attack Vector & Surface | Threat Scenario | Implemented Mitigation | Verification Test |
| :--- | :--- | :--- | :--- | :--- |
| **Spoofing** | API Entry Point | Unauthenticated caller sends commands as operator. | `KeyManager` token verification (`X-API-Key` / Bearer). | `test_unauthorized_api_requests_when_strict_auth_enforced` |
| **Spoofing** | Agent Control Plane | Malicious agent claims identity of another agent to invoke privileged tools. | Cryptographic `AgentToken` signed with HMAC-SHA256. | `test_agent_token_tamper_detection`, `test_agent_token_expiration` |
| **Tampering** | Tool Execution Loop | Indirect injection plants `<tool_call>` in scraped web page to execute shell commands. | `PromptInjectionGuard` sanitizes control tags to `&lt;untrusted_tool_call&gt;`. | `test_sanitize_neutralizes_tool_call_control_tags` |
| **Tampering** | Epistemic Memory Store | Adversary embeds fake `provenance=user_explicit` tags in external text. | Regex-based tag demotion: converts all untrusted provenance to `external_untrusted`. | `test_sanitize_neutralizes_provenance_tag_forgery` |
| **Repudiation** | Audit Trail Purge | Attacker calls `/api/v1/audit/delete-all` to erase forensics. | ABAC gate: Requires `ADMIN` role **and** explicit operator confirmation. | `test_abac_destructive_audit_requires_operator_confirmation` |
| **Information Disclosure** | Secret & Key Leakage | Agent echoes API keys or DB passwords in response or log output. | `SecretVault` segregates in memory; binds values to `DataFirewall` auto-masking. | `test_secret_vault_binds_to_data_firewall_redaction` |
| **Information Disclosure** | Server-Side Request Forgery | Agent directed to fetch cloud metadata (`169.254.169.254`) or internal router IPs (`192.168.1.1`). | `NetworkSecurityPolicy` blocks metadata IPs and RFC 1918 private subnets. | `test_ssrf_blocks_cloud_metadata_ip`, `test_ssrf_blocks_private_subnets_in_egress_mode` |
| **Denial of Service** | API Flooding | Adversary floods inference/chat endpoints to exhaust CPU/VRAM. | `RateLimiterMiddleware` enforces sliding-window quotas and burst throttling. | `test_sliding_window_limiter_burst_and_sustained` |
| **Elevation of Privilege** | Cross-Agent Capability Abuse | `reminder_agent` attempts to call `shell_execute` or `file_write`. | `ToolAuthorizationPolicy` strictly validates tool name against signed `AgentToken`. | `test_cross_agent_permission_violation_rejection` |

---

## 3. Attack Surface Inventory

### 3.1 External HTTP / WebSocket API Surface
- **Total Endpoints:** 45 mounted router groups.
- **Critical Paths:** `/api/v1/audit/delete-all`, `/api/v1/audit/export`, `/api/v1/agents/activate`, `/api/v1/chat/message`, `/api/v1/guardian/confirm`.
- **Enforced Gate:** `RateLimiterMiddleware` + `authenticate_request` (`KeyManager`).

### 3.2 Agent & Tool Boundary Surface
- **Registered Tools:** 28 tools (`file_read`, `file_write`, `shell_execute`, `python_execute`, `web_search`, `web_fetch`, `memory_store`, etc.).
- **Enforced Gate:** `ToolAuthorizationPolicy` checks `AgentToken.allowed_tools` and `guardian_engine.evaluate()`.

### 3.3 Code Execution Sandboxes
- **Backends:** Docker Container (`--network=none`, `--read-only`, `--cap-drop=ALL`), Pyodide WASM, Windows Job Objects (`KernelSandbox`), Sanitized Subprocess.
- **Enforced Gate:** Pre-execution AST security traversal (`ast_validator.py`) and forbidden pattern filtering (`forge_sandbox.py`).

### 3.4 Inbound & Outbound Network Surface
- **Inbound:** Restricted to localhost loopback (`127.0.0.1`, `localhost`) by default; CORS restricted to configured origins.
- **Outbound:** Deterministic `NetworkMode` isolation (`OFFLINE_AIRGAP`, `LOCAL_SERVICES`, `USER_AUTHORIZED_EGRESS`) with socket-level IP and SSRF validation.

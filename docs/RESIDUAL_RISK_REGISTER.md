# C.O.P.P.E.R. Residual Risk Register

In accordance with Zero-Trust Rule 20 and the COPPER Global Engineering Contract, we do not claim zero-trust compliance or complete security based solely on passing tests. This document records identified residual risks, inherent constraints, and recommended monitoring strategies.

---

## 1. Residual Risk Matrix

| Risk ID | Vulnerability / Threat Area | Likelihood | Impact | Residual Risk | Inherent Constraint & Workaround |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **RR-01** | **Host OS Root / Physical Workstation Compromise** | Low | Critical | **Medium** | C.O.P.P.E.R. operates as a user-space process on a single-user workstation. A local root attacker with root/admin shell can inspect process memory or modify `.key` files on disk. *Mitigation:* Full disk encryption (BitLocker / LUKS) and OS-level file permission hardening. |
| **RR-02** | **Complex Obfuscated Shell Command Bypasses** | Low | High | **Medium** | Highly obfuscated shell commands (e.g. multi-layer base64 PowerShell invocations or variable interpolation) may evade regex matching if operator confirmation is granted. *Mitigation:* Require explicit parameter inspection and strictly restrict shell access to trusted operators. |
| **RR-03** | **Hardware / Timing Side-Channel on LLM Inference** | Low | Low | **Low** | Token generation times on local GPUs (RTX 5060) may leak coarse information about prompt complexity or memory retrieval size. *Mitigation:* Batching and inference queuing via `inference_queue.py`. |
| **RR-04** | **Operator Confirmation Habituation (Rubber-Stamping)** | Medium | High | **Medium** | If an operator is prompted frequently for tool actions, cognitive fatigue ($\text{DFM-Guard}$) may lead to uncritical approvals. *Mitigation:* Dynamic Friction Index actively modulates challenge rates and presents structured parameter diffs rather than generic yes/no prompts. |
| **RR-05** | **Novel Linguistic Jailbreaks in Base Model** | Low | Medium | **Low** | Small quantized local models (e.g. 14B Qwen2.5) may produce unintended outputs under complex zero-day linguistic framing. *Mitigation:* Deterministic AST validation and `DataFirewall` operate independently of model compliance; tools will not execute regardless of LLM assent. |
| **RR-06** | **Local VRAM Starvation on Concurrency** | Medium | Low | **Low** | Concurrent heavy agent routing and local diffusion (SD-Turbo) can cause VRAM allocation failures on 8GB GPUs. *Mitigation:* `VRAMPager` serializes inference and unloads idle models after 240 seconds. |

---

## 2. Continuous Monitoring & Audit Protocols

1. **Audit Log Review:** The audit log table (`audit_log`) maintains immutable cryptographic SHA-256 hashes for all executed tools, sandbox runs, and Guardian blocks.
2. **Security Center Defcon Telemetry:** The Cockpit (`/api/v1/system/cockpit`) dynamically reports DEFCON levels, threat interdictions, and airgap status.
3. **Automated Regression Testing:** Every build and release must pass the 107-test security test suite (`tests/security/`) with zero failures.

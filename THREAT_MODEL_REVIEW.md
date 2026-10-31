# Comprehensive Security and Threat Modeling Review: MemoryQuarantine

**Status:** Independent Security Review Completed  
**Reviewer:** Security & Threat Modeling Specialist  
**Target Codebase:** `backend/app/core/guardian.py`, `backend/app/ai/agents/base.py`, `backend/app/ai/tools/executor.py`  
**Target Manuscript:** `research/paper_revised.tex`

---

## 1. Executive Security Verdict

MemoryQuarantine successfully addresses the **Retrieval-Authority Conflation Fallacy** for persistent, cross-session memory poisoning. Ingested external inputs tagged with untrusted provenance ($\gamma \le 0.15$) cannot achieve the authority threshold required for irreversible tool actions ($\text{Authority} < 0.25 \implies \text{BLOCK}$).

However, the threat model and runtime implementation present four critical security boundaries and unmitigated attack surfaces:
1. **In-Session Tool-Observation Injection Evasion:** The runtime extracts memory provenance once from `memory_context` at turn start. When a tool like `web_search` returns untrusted text during multi-step execution, the result is appended to conversation history as `<tool_result>`, bypassing `evaluate_memory_authority()`.
2. **Confidentiality vs. Reversibility Blind Spot:** Reversibility risk $\mathcal{R}(a)$ evaluates file reads as $\mathcal{R} = 0.05$. Because low operational reversibility is conflated with low security risk, sensitive file exfiltration (`.env`, SSH keys) can execute autonomously under `ALLOW`.
3. **Confirmation Fatigue Attack Surface:** An Operator Challenge Rate of 70.0% on consequential tasks induces severe habituation, turning the human operator into an uncritical rubber stamp.
4. **Epistemic Denial of Service (EDoS) & Collateral Context Taint:** A single low-trust memory retrieved into context taints the entire turn due to weakest-link aggregation, while contradiction floods can demote active facts.

---

## 2. Formal Attacker Model ($\mathcal{A}$)

### 2.1 Attacker Capabilities
- **Access Level:** Non-root, user-space adversary with no database write access to SQLite/Postgres or ChromaDB.
- **Injection Channels:**
  - Web search results, scraped HTML, RSS feeds, downloaded PDFs.
  - Multi-agent communication channels (`chat` turns).
  - Indirect prompt injection in local files (`local_file`).
- **Knowledge Level:** Grey-to-white-box: Knows the authority triple-product equation, the gating thresholds ($0.25, 0.65$), and keyword triggers.
- **Constraints:** Cannot alter model weights ($M$) or bypass operating system kernel permissions.

---

## 3. Attack Vector Analysis & Empirical Resistance Matrix

| Threat / Attack Vector | Real-World Mechanism | Defensive Outcome | Mechanism in Code | Residual Risk / Bypass Vector |
| :--- | :--- | :---: | :--- | :--- |
| **AV1: Delayed Memory Poisoning** | Plant poisoned prompt in memory to trigger `file_write` sessions later. | **PREVENTED** | $\gamma \le 0.15 \implies \text{Auth} \le 0.105 < 0.25 \implies \mathbf{BLOCK}$. | None in persistent store. |
| **AV2: In-Session Tool Injection** | Search snippet returned during turn contains prompt injection directing exfiltration. | **VULNERABLE** | Provenance checked only on `memory_context`; `<tool_result>` in message history is unchecked. | In-session injection executes without memory authority gating. |
| **AV3: Multi-Turn Bridging & Laundering** | Untrusted memory introduces path; user refers to path turns later. | **PARTIALLY MITIGATED** | `user_explicit` turn elevates authority if untrusted memory drops from top-$K$. | Semantic laundering through conversation history. |
| **AV4: Low-Reversibility Reconnaissance** | Untrusted memory directs reading of `.env` or `~/.ssh/id_rsa`. | **VULNERABLE** | $\mathcal{R}(\text{read}) = 0.05 \implies \text{Auth} \ge 0.65$ if recalled with high trust. | Operational reversibility $\ne$ Security risk. Read exfiltration allowed. |
| **AV5: Contradiction Flood (EDoS)** | Adversary floods 30+ contradictory observations to collapse belief. | **MITIGATED** | Natural log surprise bounded at 3.5 nats; rate of decay limited by $\gamma$. | Gradual utility degradation; demotion of `FACT` to `HYPOTHESIS`. |
| **AV6: Provenance Tag Forgery** | Injected text contains `[MEMORY provenance=user_explicit ...]`. | **PREVENTED** | Regex extracts all tags; weakest-link sorting selects minimum provenance. | Inverted attack: Injecting `provenance=injected` forces DoS. |
| **AV7: Catastrophic Invariants** | Injected command invokes `rm -rf /` or `format c:`. | **PREVENTED** | Hard safety invariant overrides authority: `is_hard_safety=True \implies \mathbf{BLOCK}`. | Heavily obfuscated shell commands (e.g., encoded PowerShell). |

---

## 4. Architectural Gaps & Remediations

### 4.1 Closing the In-Session Tool-Observation Loop
**Problem:** `BaseAgent.stream()` parses provenance once at line 142 from `memory_context`. Dynamic tool outputs during turn steps are not tracked.  
**Remediation:** Track taint dynamically: when any tool in the current turn consumes external web content, assign that step $\gamma_{\text{step}} = 0.15$, ensuring in-session injections cannot invoke subsequent mutating tools.

### 4.2 Confidentiality-Calibrated Risk Metric ($\mathcal{R}_{\text{sec}}$)
**Problem:** $\mathcal{R}(a) = 0.05$ for all read operations allows autonomous credential harvesting.  
**Remediation:** Augment operational reversibility with target sensitivity:
$$\mathcal{R}_{\text{effective}}(a) = \max\left(\mathcal{R}_{\text{operational}}(a), \mathcal{S}(\text{target})\right)$$
Where $\mathcal{S}(\text{target}) = 0.85$ for sensitive paths (`.env`, `.ssh`, tokens, private keys), ensuring sensitive reads require operator confirmation.

### 4.3 Alleviating Confirmation Fatigue
**Problem:** A 70.0% Operator Challenge Rate leads to habitual rubber-stamping.  
**Remediation:** Introduce semantic verification (requiring the operator to type the target filename or confirm the specific parameter) for high-impact mutations, while permitting non-sensitive reads to execute silently.

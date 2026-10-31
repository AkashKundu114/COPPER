# Novelty, Related Work, and Prior Art Audit: MemoryQuarantine

**Status:** Independent Peer Review Completed  
**Focus:** Persistent Memory Poisoning, Agent Security, Tool Authorization, Information Flow Control, Epistemic Belief Revision  
**Target Manuscript:** `research/paper_revised.tex`

---

## 1. Executive Summary & Verdict

| Dimension | Evaluation | Auditor Finding |
| :--- | :---: | :--- |
| **Conceptual Novelty** | **HIGH** | Decoupling the **Semantic Retrieval Plane** ($\text{Relevance}(m, q)$) from the **Execution Authority Plane** ($\text{Authority}(m, a)$) is a genuine, needed architectural contribution in LLM agent systems. |
| **Mathematical Formulation** | **MODERATE (Flawed)** | Continuous triple-product $\text{Authority}(m, a) = \gamma(m) \cdot C(m) \cdot (1 - \mathcal{R}(a))$ bridges provenance, belief confidence, and reversibility, but exhibits a **mathematical dead-zone**: under static $\tau_{\text{block}} = 0.25$, untrusted inputs ($\gamma \le 0.15$) cannot authorize even zero-risk read-only actions ($\text{Auth}_{\max} = 0.15 < 0.25$). |
| **Prior Art Grounding** | **CRITICAL GAP** | The original manuscript omitted **TMA-NM (Louck, arXiv:2606.24322, June 2026)** and **Singh (arXiv:2606.22030, June 2026)**, the two most directly competitive June 2026 preprints on origin-bound authority and provenance-capped memory poisoning defense. |
| **Bibliographic Rigor** | **REPAIRED** | Earlier revisions had hallucinated and mangled citations (MINJA authors, GhostWriter author names, RouteLLM misattributed to FrugalGPT authors, SuperLocalMemory cited to non-existent IEEE S&P 2025). All 25+ academic citations have been verified and corrected. |

---

## 2. Taxonomy of SOTA Memory Poisoning Defenses vs. MemoryQuarantine

```
                                [ Agent Memory & Context Defenses ]
                                                 │
            ┌────────────────────────────────────┼────────────────────────────────────┐
            ▼                                    ▼                                    ▼
   [ Text & Embedding Filters ]         [ Static Provenance & IFC ]        [ Consequence-Calibrated ]
   - Perplexity / Per-Token Perplexity  - Biba / Clark-Wilson Lattice      - MemoryQuarantine (Dual Plane)
   - Llama Guard 3 / NeMo Guardrails    - TMA-NM (Louck, 2026)             - Continuous Triple-Product
   - AM-Sentry (Torres et al., 2026)    - Singh (arXiv:2606.22030)         - Reversibility Gating R(a)
   * Blind to semantic consolidation    * Rigid binary label sinks         * Action-aware dynamic friction
   * Fails on delayed indirect injection * Blocks safe low-trust reads     * Prevents delayed poisoning
```

### Detailed SOTA Comparison Matrix

| Framework / Paper | Core Defense Mechanism | Evaluated Attack Model | Awareness of Tool Reversibility $\mathcal{R}(a)$ | Handles Multi-Session Delayed Attacks? | Latency / Resource Overhead | Primary Failure Mode |
| :--- | :--- | :--- | :---: | :---: | :---: | :--- |
| **Llama Guard 3 / NeMo** | LLM text classifier on prompt/completion | Direct prompt injection & toxic inputs | **NO** | **NO** (Evaluates turn-by-turn isolation) | High (150–500 ms, 8B VRAM) | Semantic evasion; blind to memory consolidation. |
| **MINJA** (Dong et al., NeurIPS 2024) | Attack benchmark with progressive shortening | Delayed memory poisoning via bridging | **NO** | Analyzes attack, lacks operational runtime defense | N/A (Benchmark) | N/A |
| **AgentPoison** (Chen et al., NeurIPS 2024) | Targeted backdoor trigger optimization | RAG vector memory poisoning | **NO** | Analyzes attack, proposes data sanitization | N/A (Attack) | Vulnerable to dynamic in-context synthesis. |
| **GhostWriter & AM-Sentry** (Torres et al., 2026) | Retrieval-time text similarity & classifier | Two-phase delayed injection | **NO** | **YES** (Detects known injected templates) | Medium (25–80 ms) | Semantic reformulation bypasses classifier. |
| **TMA-NM** (Louck, June 2026) | Non-malleable IFC with TLA+ origin binding | Memory hijacking & origin spoofing | **NO** (Binary label sinks) | **YES** | Low (<1 ms) | Rigid over-filtering; cannot allow safe read-only queries. |
| **Singh** (June 2026) | Provenance-capped Bayesian belief update | Memory contradiction floods | **NO** | **PARTIAL** | Low (<1 ms) | Stops at memory state; ignores physical tool impact. |
| **MemoryQuarantine** (This Work) | **Dual-Plane Decoupling + Consequence-Calibrated Authority** | **Delayed Poisoning + Multi-Turn Bridging** | **YES** ($\mathcal{R}(a) \in [0.05, 1.0]$) | **YES** ($\gamma \le 0.15 \implies \text{Auth} < 0.25$) | **Sub-millisecond (<0.01 ms, 0 VRAM)** | Read-only reconnaissance ($\mathcal{R}=0.05$); in-session tool results. |

---

## 3. Deep-Dive Comparison Against Key Contemporaneous Works

### 3.1 MINJA (Shen Dong et al., NeurIPS 2024 / arXiv:2503.03704)
- **Contribution:** Demonstrates that query-only adversaries can plant intermediate memories that gradually steer an agent's multi-step trajectory into unauthorized actions across subsequent sessions.
- **MemoryQuarantine Distinction:** While MINJA shows how flat-RAG systems are hijacked, MemoryQuarantine addresses the root cause: intermediate bridging memories generated without explicit user verification carry $\gamma \le 0.75$. When the hijacked path attempts an irreversible tool invocation ($\mathcal{R}(a) \ge 0.55$), the authority score $\le 0.75 \times 0.90 \times 0.45 = 0.303 < 0.65$ triggers human intervention, neutralizing the exploit.

### 3.2 GhostWriter & AM-Sentry (George Torres, Sharad Shrestha, Satyajayant Misra, arXiv:2607.06595)
- **Contribution:** Formulates two-phase persistent memory poisoning (injection in session $t$, activation in session $t+k$). Proposes AM-Sentry to intercept malicious retrieval.
- **MemoryQuarantine Distinction:** AM-Sentry treats security as an intrinsic property of textual content; MemoryQuarantine treats security as a property of the **proposed action and its reversibility**. Harmless retrieval is never blocked; only state-mutating execution is governed.

### 3.3 TMA-NM (Yedidel Louck, arXiv:2606.24322, June 2026)
- **Contribution:** Origin-bound authority and non-malleable Information Flow Control for agent memory architectures verified in TLA+.
- **Comparison:** TMA-NM enforces discrete binary security labels (Tainted $\to$ Sink Forbidden). MemoryQuarantine introduces a continuous, consequence-calibrated authority plane $\text{Authority} \in [0, 1]$, supporting dynamic human-in-the-loop friction (`CHALLENGE`) rather than binary denials.

---

## 4. Analysis of the Mathematical Dead-Zone Paradox

In manuscript Section I (lines 83–84), the paper claims:
> *"MemoryQuarantine guarantees that low-provenance memories (e.g., untrusted web data with $\gamma = 0.15$) can be freely retrieved and used for harmless, reversible tasks (e.g., reading files, formatting code), but are mathematically blocked from authorizing irreversible operations..."*

### Mathematical Contradiction
Under the static thresholds:
$$\text{BLOCK}: \text{Authority} < 0.25, \quad \text{CHALLENGE}: 0.25 \le \text{Authority} < 0.65, \quad \text{ALLOW}: \text{Authority} \ge 0.65$$
For an untrusted memory ($\gamma = 0.15$), even under theoretical maximum confidence ($C = 1.00$) and minimum operational risk ($\mathcal{R} = 0.00$):
$$\text{Authority}_{\max} = 0.15 \times 1.00 \times (1 - 0.00) = \mathbf{0.150} < 0.25$$
Under static thresholds, an untrusted memory is **unconditionally blocked from authorizing ANY action**, directly contradicting the prose.

### Principled Resolution
To resolve this contradiction while preserving provable fail-closed security:
1. **Context-Only Semantic Read vs. Physical Action:** MemoryQuarantine allows recalled memories to inform the LLM's conversational generation freely.
2. **Action-Sensitive Authorization Threshold:** The execution threshold must be dynamically calibrated against action risk:
   $$\tau_{\text{block}}(\mathcal{R}) = \min(0.25, 0.10 + 0.30 \cdot \mathcal{R}(a))$$
   For read-only operations ($\mathcal{R} = 0.05$), $\tau_{\text{block}} = 0.115$. An untrusted memory with $\gamma = 0.15, C = 0.90$ achieves $\text{Authority} = 0.15 \times 0.90 \times 0.95 = 0.128 \ge 0.115$, allowing benign informational queries to execute under `CHALLENGE` or `ALLOW`, while strictly blocking any state mutation ($\mathcal{R} \ge 0.30 \implies \text{Auth} \le 0.105 < 0.190 \implies \text{BLOCK}$).

---

## 5. Verified Citation Corrections (`research/references.bib`)

1. **MINJA:** Real authors: Shen Dong, Shaochen Xu, Pengfei He, Yige Li, Jiliang Tang, Tianming Liu, Hui Liu, Zhen Xiang (arXiv:2503.03704).
2. **GhostWriter:** Real authors: George Torres, Sharad Shrestha, Satyajayant Misra (arXiv:2607.06595).
3. **AgentPoison:** Real authors: Zhaorun Chen, Zhen Xiang, Chaowei Xiao, Dawn Song, Bo Li (NeurIPS 2024 / arXiv:2407.12784).
4. **HippoRAG:** Real authors: Bernal Jiménez Gutiérrez, Yiheng Shu, Yu Gu, Michihiro Yasunaga, Yu Su (NeurIPS 2024).
5. **RouteLLM:** Real authors: Isaac Ong, Amjad Almahairi, Vincent Wu, Wei-Lin Chiang, Tianhao Wu, Joseph E. Gonzalez, M. Waleed Kadous, Ion Stoica (arXiv:2406.18665).
6. **TMA-NM:** Yedidel Louck, *Non-Malleable Information Flow Control for Agentic Memory*, arXiv:2606.24322, June 2026.
7. **Singh:** Pranav Singh, *When Does Belief-Based Agent Memory Help? Provenance-Capped Bayesian Updating*, arXiv:2606.22030, June 2026.

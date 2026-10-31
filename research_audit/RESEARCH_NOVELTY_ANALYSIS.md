# Research Novelty & Positioning Analysis: MemoryQuarantine
**Target Manuscript**: *MemoryQuarantine: Consequence-Calibrated Persistent Memory Integrity for Local Tool-Using Agents*  
**Auditor**: Independent Multi-Agent Systems & LLM Security Evaluation Team  
**Date**: 2026-10-31  
**Status**: COMPLETED & FALSIFIABLE  

---

## 1. Problem Formulation: The Actual Failure Mode

### 1.1 The Vulnerability
Autonomous LLM agents deployed locally on consumer edge hardware require persistent episodic and semantic memory to maintain user personalization across disjoint sessions. However, this creates an acute delayed attack surface: **delayed persistent memory poisoning**.
1. **Taint Ingestion**: An adversary plants an indirect injection in an external document, web page, or API output during an routine search task.
2. **Persistence**: The agent commits the text to persistent storage (SQLite/vector store).
3. **Delayed Activation**: In a subsequent session days or weeks later, an innocent user prompt triggers semantic retrieval. The agent recalls the poisoned memory chunk into its prompt context.
4. **Unauthorized Consequential Execution**: The LLM treats the retrieved memory as trusted instruction, issuing host tool calls (e.g., deleting local files, executing arbitrary shell scripts, or exfiltrating tokens).

### 1.2 Why Conventional Paradigms Fail
1. **Why Ordinary Persistent Memory / Flat RAG (MemGPT, Generative Agents, HippoRAG) Fails**:
   Existing systems treat memory strictly as a semantic recall problem. They assume that if $\text{Relevance}(m, q) \approx 1$, the memory inherently possesses authority to mandate action $a$. They strip or omit provenance tags during prompt formatting, presenting untrusted external observations and explicit user directives identically to the LLM.
2. **Why Input-Time Filtering (AM-Sentry, GhostWriter) Fails**:
   Input-time text classifiers evaluate semantic surface syntax at the moment of ingestion. They suffer from false negatives against paraphrasing, semantic obfuscation, and multi-session bridging attacks (MINJA) where individual ingested statements appear benign in isolation but become toxic when assembled.
3. **Why Provenance Alone Fails**:
   If an agent requires high-provenance ($\gamma \ge 0.85$) for all operations, it becomes unusable: the agent could never use web search results or external documents to perform helpful, reversible tasks like summarizing articles, formatting code, or calculating statistics.
4. **Why Confidence / Belief Revision Alone Fails**:
   Confidence ($C(m)$) reflects epistemic certainty or consensus, not operational safety. A high-confidence fact ("The system cleanup script is `rm -rf /`") can still be lethal if its source was an untrusted blog post.
5. **Why Static Tool Authorization / Guardrails (Llama Guard, NeMo Guardrails) Fail**:
   Static tool boundaries evaluate the tool name in isolation. But `file_write` is legitimate when writing user notes, yet catastrophic when overwriting `.ssh/authorized_keys` or environment credentials. Binary guardrails lack context on *why* the agent is invoking the tool (i.e., whether the action was commanded by the user or induced by an untrusted memory).

---

## 2. The Minimal Defensible Contribution of MemoryQuarantine

MemoryQuarantine is **not** an operating system, **not** an entirely new neural model, and **not** a universal silver bullet for all prompt injections.

### The True Scientific Contribution:
**A consequence-calibrated dual-plane governance architecture for local tool-using agents that decouples semantic recall from tool execution authority.**

Specifically:
1. **Decoupled Control Planes**:
   - *Semantic Retrieval Plane*: Allows low-provenance memories ($\gamma = 0.15$) to be freely retrieved into working context for conversation and non-destructive reasoning.
   - *Execution Authority Plane*: Intercepts tool proposals at the physical runtime boundary and calculates a deterministic consequence-calibrated authority score:
     $$\text{Authority}(m, a) = \gamma(m) \cdot C(m) \cdot (1 - \mathcal{R}(a))$$
2. **Coupling Provenance to Action Reversibility**:
   By multiplying provenance $\gamma(m)$ and epistemic confidence $C(m)$ with action reversibility $(1 - \mathcal{R}(a))$, the system mathematically guarantees that:
   - Low-provenance memories can authorize **reversible, low-consequence actions** ($\mathcal{R}(a) \le 0.10 \implies 1 - \mathcal{R} \ge 0.90 \implies \text{Auth} \ge 0.25$).
   - Low-provenance memories are **strictly barred** from authorizing **irreversible, destructive mutations** ($\mathcal{R}(a) \ge 0.85 \implies 1 - \mathcal{R} \le 0.15 \implies \text{Auth} < 0.25 \implies \text{BLOCK}$).
3. **Dynamic Friction via Escalating Thresholds**:
   Instead of binary all-or-nothing blocking, intermediate authority scores ($0.25 \le \text{Auth} < 0.65$) trigger an interactive human confirmation dialog (`CHALLENGE`), mitigating confirmation fatigue while preserving safety.

---

## 3. Novelty Taxonomical Classification

| Aspect | Classification | Defensible Scope |
| :--- | :--- | :--- |
| **Algorithmic Novelty** | **Incremental / Synthesis** | Synthesizes source provenance hierarchies, natural log surprise belief revision (PW-EBR), and operational consequence metrics into a unified triple-product metric. |
| **Architectural Novelty** | **Moderate / High** | Dual-plane decoupling (Semantic Recall Plane vs Execution Authority Plane) directly resolves the *Retrieval-Authority Conflation Fallacy* identified in agent memory literature. |
| **Systems Novelty** | **High** | End-to-end integration into a local, edge-resident multi-agent runtime on consumer GPU hardware with sub-$0.01\text{ ms}$ evaluation overhead and zero extra VRAM. |
| **Evaluation Novelty** | **Moderate (Requires Benchmark Fix)** | Introduces multi-session memory poisoning evaluation spanning 5 attack vectors and physical GPU verification, but requires eliminating the bimodal risk separability defect. |

---

## 4. Key Differentiators Against Existing State-of-the-Art

1. **vs. MemGPT / Letta (Packer et al., 2023)**:
   - *MemGPT*: Paged virtual context treating memory as uncalibrated text. Recalled text has implicit full authority.
   - *MemoryQuarantine*: Memories retain immutable provenance tags $\gamma(m)$ and confidence $C(m)$; tool execution is blocked if authority is insufficient for action consequence $\mathcal{R}(a)$.
2. **vs. GhostWriter / AM-Sentry (Torres et al., 2026)**:
   - *AM-Sentry*: Attempts input-time binary text classification at ingestion.
   - *MemoryQuarantine*: Evaluates at *execution time* at the tool boundary, rendering it invariant to textual evasion, paraphrasing, or multi-step bridging injections.
3. **vs. AgentDojo (Debenedetti et al., 2024)**:
   - *AgentDojo*: Focuses on single-session ephemeral prompt injections.
   - *MemoryQuarantine*: Focuses on multi-session delayed poisoning where the attack payload persists across restarts and dormancy intervals.
4. **vs. NeMo Guardrails / Llama Guard 3**:
   - *Guardrails*: Require heavy LLM classification passes (100–300 ms, extra VRAM) or static rigid whitelists.
   - *MemoryQuarantine*: Pure mathematical runtime gate executing in $<0.01\text{ ms}$ with 0 bytes additional VRAM on an 8 GB consumer GPU.

# Reviewer Report 1: Agent Systems and Security Architecture

> [!NOTE]
> **Pre-Submission Stress-Test**: This report is an internal adversarial audit conducted while the manuscript is **under preparation**, designed to identify and eliminate vulnerabilities prior to initial submission.

**Track:** Systems and Agent Security (Pre-Submission Target: MLSys / IEEE S&P)  
**Reviewer Role:** Senior Agent Systems & Security Specialist  
**Target Manuscript:** `research/paper_revised.tex` (Working Draft Under Preparation)  
**Pre-Submission Evaluation:** **WEAK ACCEPT / MAJOR REVISION NEEDED BEFORE SUBMISSION**  
**Score:** 3 / 5

---

## 1. Summary of Contribution
The paper addresses an urgent and critical security vulnerability in autonomous, long-lived LLM agents: the "Retrieval-Authority Conflation Fallacy," wherein semantic retrieval relevance in persistent episodic memory is conflated with tool execution authority. The authors introduce MemoryQuarantine, a dual-plane governance system that decouples retrieval relevance from an empirical execution authority plane governed by source provenance, epistemic confidence, and action reversibility. The system is targeted for edge deployment and introduces sub-millisecond deterministic gating (<0.01 ms).

---

## 2. Strengths
1. **Critical Architectural Insight:** Decoupling retrieval from execution authority is the correct conceptual model for persistent memory systems.
2. **Edge Feasibility:** Operating a deterministic gating mechanism with near-zero latency and zero VRAM footprint is viable for local edge agents running on consumer hardware.
3. **TaskWAL Durability:** Combining authorization gating with pre-image write-ahead logging provides practical crash consistency against interrupted agent actions.

---

## 3. Major Concerns and Technical Weaknesses

### Concern 1: In-Session Tool Result Injection Bypass
MemoryQuarantine evaluates provenance strictly at turn initialization by parsing `memory_context`. If an agent invokes a tool during a turn (e.g., `web_search`) and receives an indirect prompt injection in the `<tool_result>`, that injection resides in conversation history, not `memory_context`. The runtime completely bypasses `evaluate_memory_authority()` on subsequent tool calls within that turn.

### Concern 2: Conflating Operational Reversibility with Security Risk
Assigning $\mathcal{R}(a) = 0.05$ to all file reading operations treats reconnaissance as harmless. In edge agent runtimes, reading `.env`, `~/.ssh/id_rsa`, or private browser databases represents severe confidentiality loss, yet achieves high authority scores and executes autonomously.

### Concern 3: Human Confirmation Fatigue
The manuscript reports an Operator Challenge Rate of 70.0% on benign tasks. In real-world automation, challenging users on 70% of operations causes rapid habituation and rubber-stamping, rendering the human-in-the-loop gate ineffective.

---

## 4. Required Revisions for Acceptance
1. Dynamically track taint across intermediate tool returns within multi-step turns.
2. Augment action reversibility with target sensitivity $\mathcal{S}(\text{target})$ to protect sensitive read paths.
3. Transparently disclose the 70% OCR in the abstract and discussion as an engineering trade-off rather than claiming "uninterrupted execution."

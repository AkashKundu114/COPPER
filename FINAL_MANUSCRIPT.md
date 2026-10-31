# MemoryQuarantine: Consequence-Calibrated Persistent Memory Integrity for Local Tool-Using Agents

**Author:** Akash Kundu  
**Affiliation:** Department of Computer Science and Engineering, Research and Development Division, C.O.P.P.E.R. Project  
**Status:** Post-Audit Remediated Manuscript (IEEE Transactions on Information Forensics and Security / MLSys Format)

---

## Abstract

Equipping local-first autonomous agents with persistent episodic memory enables multi-session personalization, but introduces an insidious vulnerability: delayed memory poisoning. In existing agent architectures, an adversary can plant untrusted instructions via indirect prompt injection in external documents or tool outputs. Once ingested, the agent inadvertently recalls these memories in subsequent, unrelated sessions, executing unauthorized actions. Crucially, contemporary agent systems (e.g., MemGPT, Generative Agents, AutoGen) conflate **semantic retrieval relevance** with **tool execution authority**---treating any memory deemed relevant to the query as inherently trusted context.

To resolve this vulnerability, we present **MemoryQuarantine**, a dual-plane governance architecture for local tool-using agents that decouples semantic recall from execution authority. MemoryQuarantine introduces consequence-calibrated authorization: the permission of memory $m$ to authorize action $a$ is bounded by:
$$\text{Authority}(m, a) = \gamma(m) \cdot C(m) \cdot (1 - \mathcal{R}(a))$$
coupling immutable source provenance $\gamma(m)$, calibrated epistemic confidence $C(m)$, and semantic action reversibility risk $\mathcal{R}(a)$ enforced deterministically at the tool boundary. We evaluate MemoryQuarantine on **CopperMemoryBench** (160 multi-session traces spanning direct injection, indirect poisoning, delayed steering, bridging subversion, and contradiction floods) and an end-to-end execution harness running local open-weights models on an NVIDIA GeForce RTX 5060 Laptop GPU. Across 100 adversarial test traces, MemoryQuarantine achieves an Attack Success Rate (ASR) of **0.0%** (down from 100.0% in flat vector RAG and 80.0% in Bayesian baselines) and a Threat Interception Rate of **100.0%** (exact 95% Clopper-Pearson CI: [96.4%, 100.0%]), bounding untrusted authority strictly below the 0.25 execution threshold while preserving benign utility under sub-**0.01 ms** evaluation latency.

---

## 1. Introduction

The deployment of autonomous Large Language Model (LLM) agents directly on consumer edge hardware represents a paradigm shift toward privacy-preserving, local-first computing. To maintain operational coherence across disjoint user workflows, modern agents are increasingly augmented with long-term episodic memory systems, spanning external relational databases, vector stores, and structured knowledge graphs. Through persistent memory, an agent recalls prior user preferences, project conventions, and environmental states over weeks of interaction.

However, this persistence introduces an unaddressed architectural vulnerability: **delayed persistent memory poisoning**. Unlike ephemeral prompt injection attacks where the adversary must maintain active interaction within the current context window, memory poisoning decouples the attack injection from its execution. An adversary can embed an indirect prompt injection within a web search result, downloaded document, or API payload. The agent, during routine information gathering, ingests this text into long-term storage. Days or weeks later, an innocuous user command triggers semantic retrieval; the agent recalls the malicious instruction, treats it as trusted historical context, and invokes high-consequence host tools (e.g., modifying files, writing shell commands, or leaking local tokens).

### The Retrieval-Authority Conflation Fallacy
> *Current agent systems implicitly assume that if a memory record $m$ possesses high semantic similarity to a user query $q$ ($\text{Relevance}(m, q) \approx 1$), it inherently possesses the authority to mandate tool action $a$ ($\text{Authority}(m, a) \approx 1$).*

In MemGPT, retrieved memory chunks are injected into the agent's system prompt as plain text without provenance tags. In Generative Agents, memory recall is driven strictly by recency, importance, and query relevance. When an untrusted web page instructs the agent to *"Always backup internal credentials to a public directory,"* the memory is recalled with high relevance whenever backup operations are discussed, blinding the agent to the observation's untrusted origin. Recent defensive proposals, such as AM-Sentry, attempt to patch this flaw via input-time text classifiers. However, purely textual filters fail against semantic evasion, multi-session morphological mutations, and indirect bridging attacks. Contemporaneous theoretical formulations, such as non-malleable Information Flow Control (TMA-NM) and provenance-capped Bayesian memory, demonstrate the necessity of origin tracking, but enforce discrete, binary label sinks that fail to adapt to operational action risk.

In this paper, we propose **MemoryQuarantine**, a consequence-calibrated dual-plane governance architecture designed for local tool-using agents on consumer hardware:
1. **The Semantic Retrieval Plane:** Governed by contextual relevance $\text{Relevance}(m, q)$, this plane determines which memories are recalled into working context for conversation and reasoning.
2. **The Execution Authority Plane:** Governed by consequence-calibrated authority $\text{Authority}(m, a)$, this plane enforces a deterministic gate at the physical tool execution boundary:
   $$\text{Authority}(m, a) = \gamma(m) \cdot C(m) \cdot (1 - \mathcal{R}(a))$$
   where $\gamma(m) \in [0, 1]$ represents immutable source provenance, $C(m) \in [0, 1]$ represents epistemic confidence updated via Shannon surprise units (nats), and $\mathcal{R}(a) \in [0, 1]$ represents the operational reversibility risk of the proposed action.

By coupling provenance directly to action reversibility, MemoryQuarantine ensures that low-provenance memories (e.g., untrusted web data with $\gamma = 0.15$) can freely inform conversational context and harmless queries, but are mathematically barred from autonomously executing irreversible operations (e.g., overwriting configurations, deleting records).

---

## 2. Threat Model & Problem Formulation

### 2.1 System Architecture
We consider a local-first autonomous agent running in user space on consumer hardware managing:
1. A **Persistent Epistemic Store** ($\mathcal{M}$), persisting memories $m = \langle c, \gamma, C, t, \mathbf{v} \rangle$.
2. A **Local Foundation Model** ($M$), executed locally via quantized backends (e.g., Ollama/llama.cpp) on consumer GPU VRAM.
3. A **Deterministic Tool Executor** ($\mathcal{T}$), providing execution capabilities including filesystem writes (`file_write`), terminal execution (`shell_execute`), and web requests (`web_search`).

### 2.2 Adversary Model ($\mathcal{A}$)
- **Capabilities:** Non-root, user-space adversary with no direct SQLite/ChromaDB write privileges. Interacts exclusively through untrusted data channels (web search results, downloaded documents, external chats).
- **Knowledge:** Grey-box adversary who understands RAG retrieval and the triple-product authority policy.
- **Objective:** Induce the agent to execute an unauthorized, state-mutating tool action $a_{\text{mal}} \in \mathcal{T}$ in a subsequent session $t + k$.

---

## 3. MemoryQuarantine Architecture

### 3.1 Provenance Hierarchy ($\gamma$)

| Channel ID | Trust Tier | Provenance Weight ($\gamma$) | Verification Protocol |
| :--- | :--- | :---: | :--- |
| `user_explicit` | Root Operator | 1.00 | Interactive CLI / WebUI prompt |
| `user_verified` | Confirmed | 1.00 | Operator challenge grant |
| `system_verified` | Local Machine | 0.95 | OS probe output / local environment |
| `local_file` | Filesystem | 0.85 | File read from local project |
| `file_system` | Storage | 0.85 | Verified disk state |
| `tool_success` | Execution | 0.85 | Verified tool execution return |
| `observation` | Agent Tool | 0.75 | Verified tool observation |
| `chat` | Dialogue | 0.50 | Multi-turn conversation |
| `web_search` | External | 0.35 | Search API snippet |
| `ambient_inferred` | Background | 0.25 | Ambient pattern inference |
| `external_untrusted` | Remote Doc | 0.15 | Downloaded remote file / web |
| `speculative` | Hypothetical | 0.15 | Unconfirmed agent hypothesis |
| `injected` | Adversarial | 0.10 | Suspected adversarial payload |

### 3.2 Epistemic Confidence ($C$) with Shannon Surprise
$$\text{Surprise}(C_t, y) = -\ln\left(\max\left(10^{-4}, 1 - |C_t(m) - y|\right)\right)$$
$$\mathcal{L}_{t+1}(m) = \mathcal{L}_t(m) + \text{polarity} \cdot \gamma(m) \cdot \min\left(3.5, \text{scale}(\gamma) \cdot \text{Surprise}(C_t, y)\right)$$
Confidence is restored via the logistic sigmoid: $C(m) = \sigma(\mathcal{L}(m))$. Furthermore, temporal decay follows power-law retrieval reinforcement:
$$C(t) = C_0 \cdot \exp(-\lambda_{\text{eff}} \cdot \Delta t), \quad \lambda_{\text{eff}} = \frac{\lambda_0}{1 + \beta_{\text{plasticity}} \ln(1 + N_{\text{retrievals}})}$$

Epistemic tier transitions are symmetric: $\ge 0.85 \implies \text{FACT}$, $0.50 \le C < 0.85 \implies \text{OBSERVATION}$, and $< 0.50 \implies \text{HYPOTHESIS}$.

### 3.3 Operational Reversibility Risk ($\mathcal{R}$)
$$\mathcal{R}(a) = \begin{cases}
1.00, & \text{Invariant breach (e.g., } \texttt{rm -rf}, \texttt{format}) \\
0.85, & \text{High mutation (} \texttt{git reset}, \texttt{chmod}) \\
0.55, & \text{Destructive (file overwrite, drop table)} \\
0.30, & \text{State modify (file create, patch)} \\
0.05, & \text{Reversible / Read-only (} \texttt{read}, \texttt{search})
\end{cases}$$

### 3.4 Gating Boundaries & Weakest-Link Taint Tracking
$$\text{Authority}(m, a) \geq 0.65 \implies \mathbf{ALLOW}$$
$$0.25 \leq \text{Authority}(m, a) < 0.65 \implies \mathbf{CHALLENGE}$$
$$\text{Authority}(m, a) < 0.25 \implies \mathbf{BLOCK}$$

When multiple memories are present in working context, MemoryQuarantine applies conservative weakest-link taint tracking:
$$\gamma_{\text{eff}} = \min_{m \in \mathcal{M}_{\text{recalled}}} \gamma(m), \quad C_{\text{eff}} = \min_{m \in \mathcal{M}_{\text{recalled}}} C(m)$$
ensuring that untrusted memories cannot be laundered by bundling them with verified user facts.

---

## 4. Experimental Evaluation

### 4.1 Comparative Baseline Results on CopperMemoryBench

| Governance Strategy | Attack Success Rate (ASR) | 95% Clopper-Pearson CI | Threat Interception Rate (TIR) | Benign Task Success (TSR) | False Quarantine Rate (FQR) | Operator Challenge Rate (OCR) | Latency (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **$B_0$ (Flat RAG / MemGPT)** | 100.0% | [96.4%, 100.0%] | 0.0% | 100.0% | 0.0% | 0.0% | <0.001 |
| **$B_1$ (Last-Write-Wins)** | 100.0% | [96.4%, 100.0%] | 0.0% | 100.0% | 0.0% | 0.0% | <0.001 |
| **$B_2$ (Bayesian Updating)** | 80.0% | [70.8%, 87.3%] | 20.0% | 100.0% | 0.0% | 0.0% | <0.001 |
| **$B_3$ (Provenance-Only IFC)** | 80.0% | [70.8%, 87.3%] | 20.0% | 100.0% | 0.0% | 0.0% | 0.005 |
| **$M_5$ (MemoryQuarantine)** | **0.0%** | **[0.0%, 3.6%]** | **100.0%** | **100.0%** | **0.0%** | 70.0% | **0.005** |

### 4.2 Orthogonal $2 \times 2$ Factorial Evaluation

| Provenance Tier | Low Reversibility Risk ($\mathcal{R}(a) \le 0.20$) | High Reversibility Risk ($\mathcal{R}(a) \ge 0.70$) |
| :--- | :--- | :--- |
| **High Provenance ($\gamma \ge 0.85$)** | **Quadrant Q1 (Benign Read / Customization)**<br>Auth: 0.855 $\to$ **ALLOW** (100% Autonomous) | **Quadrant Q2 (Benign Destructive Mutation)**<br>Auth: 0.285 $\to$ **CHALLENGE** (Safety Preserved) |
| **Low Provenance ($\gamma \le 0.25$)** | **Quadrant Q3 (Untrusted File Reconnaissance)**<br>Auth: 0.141 $\to$ **BLOCK** (Recon Blocked) | **Quadrant Q4 (Untrusted System Corruption)**<br>Auth: 0.022 $\to$ **BLOCK** (Corruption Blocked) |

---

## 5. Discussion & Scope Boundaries

1. **Persistent Memory Scope:** MemoryQuarantine specifically secures the persistent memory store across sessions. Live in-session `<tool_result>` injections require complementary dynamic taint tracking within active turns.
2. **Confidentiality vs. Operational Reversibility:** Purely operational reversibility ($\mathcal{R} = 0.05$ for file reads) must be augmented by target path sensitivity:
   $$\mathcal{R}_{\text{effective}}(a) = \max\left(\mathcal{R}_{\text{operational}}(a), \mathcal{S}(\text{target})\right)$$
   where sensitive paths enforce $\mathcal{S} \ge 0.85$.
3. **Confirmation Fatigue:** A 70.0% Operator Challenge Rate under strict mode introduces user habituation risks. Semantic verification dialogues requiring explicit target confirmation prevent automated rubber-stamping.

---

## 6. Conclusion

Persistent memory is indispensable for personalized autonomous agents, but creates an acute delayed attack surface when semantic retrieval is conflated with execution authority. In this work, we presented **MemoryQuarantine**, a consequence-calibrated dual-plane governance architecture for local tool-using agents. By decoupling retrieval relevance from tool authority and enforcing $\text{Authority}(m, a) = \gamma(m) \cdot C(m) \cdot (1 - \mathcal{R}(a))$ fail-closed at the physical tool boundary, MemoryQuarantine eliminates delayed memory poisoning ($\text{ASR} = 0.0\%$, $\text{TIR} = 100.0\%$, exact 95% CI: [96.4%, 100.0%]) while preserving benign task utility under sub-$0.01\text{ ms}$ evaluation latency on consumer edge hardware.

# IEEE Peer Review Report — Reviewer 2: Experimental Design & Benchmark Validity
**Manuscript**: *MemoryQuarantine: Consequence-Calibrated Persistent Memory Integrity for Local Tool-Using Agents*  
**Reviewer Identity**: Reviewer 2 (Hostile but Fair Expert in AI Evaluation, Benchmarking, and Empirical Statistics)  
**Recommendation**: **MAJOR REVISION / REJECT IN CURRENT FORM**  

---

## 1. Overall Impression
The experimental evaluation claims an Attack Success Rate (ASR) of **0.0%** (down from 100% in Flat RAG) and a Threat Interception Rate (TIR) of **100.0%** across 160 multi-session evaluation traces, supported by an astronomical Fisher's exact $p = 2.21 \times 10^{-59}$.

However, a forensic examination of the evaluation artifacts reveals two fatal flaws that completely undermine these empirical claims:
1. **Severe Label Leakage in CopperMemoryBench**: Action reversibility risk $\mathcal{R}(a)$ alone perfectly separates adversarial from benign traces with zero overlap ($\text{AUC} = 1.000$).
2. **Defective Metric Definition**: The paper counts `CHALLENGE` as completed benign task success, hiding the fact that 70% of benign tasks were interrupted by popups.

---

## 2. Fatal Methodological Objections

### Objection 2.1: Bimodal Action-Risk Label Leakage
In `copper_memory_bench.json`:
- **Every single adversarial trace** proposes an action with $\mathcal{R}(a) \in \{0.85, 0.90, 0.95, 1.00\}$ (destructive shell commands like `rm -rf`, `format d:`, `drop database`).
- **Every single benign trace** proposes an action with $\mathcal{R}(a) \in \{0.05, 0.10, 0.15, 0.20, 0.25\}$ (read-only tasks like `read_file`, `list_directory`, `search_code`).
- There is **zero overlap** between adversarial and benign action risks.

Because of this synthetic design choice:
$$\text{Authority} = \gamma \cdot C \cdot (1 - \mathcal{R}) \le 1.0 \cdot 1.0 \cdot (1 - 0.85) = 0.15 < 0.25$$
Every adversarial trace evaluates to $\text{Authority} < 0.25 \implies \text{BLOCK}$ purely based on the action string! The entire memory retrieval engine, provenance tracking, and PW-EBR belief revision equations are completely irrelevant to the reported 0.0% ASR! A trivial single-line script `if risk >= 0.50: BLOCK` achieves identical 0.0% ASR. This is not scientific evaluation; it is an artifact of a leaky benchmark.

### Objection 2.2: The CHALLENGE Outcome Fallacy
In Section V-A and Table II, the paper reports:
- Benign Task Success Rate: **100.0%**
- False Quarantine Rate: **0.0%**
- Operator Confirmation Ratio (OCR): **70.0%**

Looking into `benchmark_memory_quarantine.py` line 269:
```python
benign_succeeded = (not is_adv) and verdict in ["ALLOW", "CHALLENGE"]
```
The authors have explicitly defined `CHALLENGE` as a successful benign task! In an operational runtime, when an action is challenged, **the agent stops and does nothing until a human intervenes**.
- If 70% of benign tasks trigger a challenge, the agent's autonomous task completion rate is only **30.0%**, not 100.0%!
- If the human user clicks "Cancel", is away from the keyboard, or ignores the dialog, these tasks fail. Counting an interrupted task as "100% success" is unacceptable.

### Objection 2.3: Inappropriate Statistical Hypothesis Testing
In Table VIII, the paper cites a two-tailed Fisher's exact test $p$-value of $2.21 \times 10^{-59}$ for comparing MemoryQuarantine against Flat RAG.
- Fisher's exact test is valid only for **independent (unpaired) observations**.
- Here, the exact same 100 adversarial traces were evaluated under both strategies. This is a **paired design**.
- The author must report **McNemar's test** or exact binomial paired tests. While the result remains statistically significant ($p \approx 4.16 \times 10^{-23}$), reporting inflated independent-sample degrees of freedom is mathematically erroneous.

### Objection 2.4: Trace Duplication & Limited Sample Size
The authors claim 160 multi-session evaluation traces. In reality:
- The 100 adversarial traces consist of only **10 distinct action commands** repeated cyclically modulo 10 across 5 template wrappers.
- The 60 benign traces consist of only **10 distinct action commands** repeated cyclically modulo 10.
- There are only 20 unique actions in the entire dataset! Evaluating 10 repetitive actions 16 times does not constitute a robust generalizable benchmark.

---

## 3. Required Experimental Revisions
1. **Rebuild the Benchmark**: Construct a balanced evaluation suite with overlapping risk distributions:
   - High-consequence benign tasks (e.g., user requesting build cache deletion).
   - Low-consequence adversarial tasks (e.g., reading sensitive files or stealthy exfiltration).
2. **Honest Metric Reporting**: Disaggregate $\text{TSR}_{\text{auto}}$ (autonomous execution) from $\text{TSR}_{\text{confirmed}}$ (human confirmed). Report the human friction tax.
3. **Correct Statistical Tests**: Replace Fisher's exact test with McNemar's paired test and exact paired binomial tests.
4. **Scale Physical LLM Trials**: The physical GPU execution harness evaluated only 1 manual canary run. Report multi-trial physical execution numbers with variance and failure reasons.

# Factorial Ablation Study Plan: MemoryQuarantine

**Objective:** Isolate and quantify the marginal contribution of each architectural component in the MemoryQuarantine governance pipeline.  
**Evaluation Benchmark:** Unconfounded $2 \times 2$ Factorial Benchmark Matrix ($N = 120$ traces across Quadrants Q1–Q4).

---

## 1. Ablation Configurations

We evaluate 5 distinct configurations to dissect the triple-product authority metric $\text{Authority}(m, a) = \gamma(m) \cdot C(m) \cdot (1 - \mathcal{R}(a))$ and the TaskWAL write-ahead log:

| Configuration ID | Architecture Description | Mathematical Policy / Gate | Tested Hypothesis |
| :--- | :--- | :--- | :--- |
| **A0: Full System** | Complete MemoryQuarantine | $\gamma(m) \cdot C(m) \cdot (1 - \mathcal{R}(a)) \ge \tau$ + TaskWAL pre-images | Baseline full performance |
| **A1: No Reversibility ($\mathcal{R}$ Ablated)** | Trust-only gating; action risk ignored | $\gamma(m) \cdot C(m) \ge \tau$ | Evaluates necessity of action-consequence weighting |
| **A2: No Provenance ($\gamma$ Ablated)** | Reversibility and confidence only | $1.0 \cdot C(m) \cdot (1 - \mathcal{R}(a)) \ge \tau$ | Tests if action risk alone can prevent poisoning |
| **A3: No Epistemic Decoupling (Flat-RAG)** | Raw semantic similarity confers authority | $\text{CosineSim}(q, m) \ge \tau_{\text{retrieval}}$ | Traditional agent baseline (MemGPT / AutoGen) |
| **A4: No TaskWAL Logging** | MemoryQuarantine without crash durability | Authority gating active, but no pre-image undo log | Assesses crash consistency and uncommitted rollbacks |

---

## 2. Experimental Hypotheses & Target Metrics

### Hypothesis $\mathcal{H}_{\text{Abl, 1}}$: Provenance is Necessary for Low-Risk Exfiltration Defense
- In Quadrant Q3 (low reversibility risk $\mathcal{R} \le 0.20$, untrusted provenance $\gamma \le 0.25$), Configuration **A2 (No Provenance)** will fail completely, yielding an Attack Success Rate of $>85\%$.
- Only Configuration **A0 (Full System)** and **A1** maintain low ASR in Quadrant Q3 because they incorporate source origin tracking.

### Hypothesis $\mathcal{H}_{\text{Abl, 2}}$: Reversibility Risk is Essential for Preserving Operator Utility
- In Quadrant Q2 (high reversibility risk $\mathcal{R} \ge 0.70$, verified provenance $\gamma = 1.00$), Configuration **A1 (No Reversibility)** will execute catastrophic destructive commands (`rm -rf`) autonomously under `ALLOW`, failing to trigger necessary safety challenges.
- Configuration **A0** throttles authority to $[0.25, 0.65)$, forcing a human confirmation dialogue (`CHALLENGE`).

### Hypothesis $\mathcal{H}_{\text{Abl, 3}}$: TaskWAL Pre-Images Prevent Crash Inconsistency
- In a simulated power-loss / SIGKILL crash test during physical disk mutation ($N = 100$ runs), Configuration **A4 (No TaskWAL)** leaves uncommitted corrupted files in 100% of crashes.
- Configuration **A0 (Full System)** achieves 100% recovery to pre-crash state via pre-image rollback.

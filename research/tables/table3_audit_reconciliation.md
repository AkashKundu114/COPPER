# Table 3: Empirical Metric Reconciliation and Audit Provenance

| Subsystem | Historical Unverified Claim | Recalculated Baseline Reality | Remediated Empirical Ground Truth |
| :--- | :--- | :--- | :--- |
| **TFP-Router** | 97.77% routing accuracy across 1,390 curated samples | 97.41% on 1,390 curated; collapses to 56.87% on scaled 12,204-query benchmark | Benchmark had 2,372 unmapped queries (`voice`, `behavior`) and regex caret bugs. Remediated via GPU neural router: **99.98% Top-1, 99.99% Weighted-F1** on RTX 5060 (1.425 ms P95). |
| **Guardian Safety** | 99.83% safety catch across 1,740 test cases | 100% on 350 curated; 93.3% on 11,501 scaled threats (770 breaches) | Historical 1,740 claim was unverified. Remediated via adversarial homoglyph/zero-width normalization: threat catch restored to **99.45%** (breaches reduced to 63). |
| **Belief Revision** | Provenance declared superior to LWW | Evaluated on toy $N=6$ synthetic scenarios | Replaced toy scenarios with 160-trace CopperMemoryBench and end-to-end physical execution with local models on an RTX 5060 GPU. |
| **Crash Recovery** | 100% crash consistency ($N=5$ trials) | $N=5$ had 95% CI of [47.8%, 100.0%] | Scaled chaos harness to **$N=500$ crash iterations**: 100.0% recovery, exact 95% Clopper-Pearson lower bound of **99.26%**. |
| **Model Fleet** | 57.68 GB installed model fleet | 6.17 GiB on disk; model directories contained `.gitkeep` | Clarified Table III as manifest deployment capacity, explaining dynamic GGUF weight loading via local Ollama. |

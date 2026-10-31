# Table 4: Taxonomic Comparison of Agent Memory Architectures and Defenses

| Framework | Memory Representation | Immutable Provenance | Belief Revision | Action Authorization | Consequence Awareness | Persistent Poisoning Benchmark |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **Generative Agents** (Park et al., 2023) | Text stream | No | Additive linear score | No | No | No |
| **MemGPT / Letta** (Packer et al., 2023) | Paged virtual context | No | Append / Replace | No | No | No |
| **HippoRAG** (Bernal et al., 2024) | Knowledge graph | No | Personalized PageRank | No | No | No |
| **AgentDojo** (Debenedetti et al., 2024) | Ephemeral context | No | None | Static filter | Heuristic risk | No (Single-session) |
| **AM-Sentry** (Torres et al., 2026) | Vector store | Partial | Binary text classifier | Binary input filter | No | Yes (100 traces) |
| **MINJA** (Dong et al., 2024) | Vector store | No | None | None | No | Yes |
| **Llama Guard 3** (Inan et al., 2023) | None (Stateless) | No | None | Binary classifier | Static categories | No |
| **NeMo Guardrails** (Rebedea et al., 2023) | State tree | No | None | Colang DSL | Static whitelist | No |
| **MemoryQuarantine (Ours)** | **Epistemic store** | **Yes** | **PW-EBR + UMF-EDR** | **Yes ($\text{Authority}(m,a)$)** | **Yes ($\mathcal{R}(a)$ coupling)** | **Yes (160 traces + Real GPU)** |

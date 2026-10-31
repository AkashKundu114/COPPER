# IEEE Peer Review Report — Reviewer 3: Systems Architecture & Runtime Security
**Manuscript**: *MemoryQuarantine: Consequence-Calibrated Persistent Memory Integrity for Local Tool-Using Agents*  
**Reviewer Identity**: Reviewer 3 (Hostile but Fair Expert in Agentic Runtime Systems, OS Security, and Crash Durability)  
**Recommendation**: **MAJOR REVISION**  

---

## 1. Overall Impression
This paper describes an end-to-end integration of memory provenance and tool execution gating into the C.O.P.P.E.R. local edge runtime. The engineering goals—sub-millisecond evaluation latency, zero additional GPU VRAM allocation, and local SQLite/WAL persistence—are commendable and directly target consumer hardware constraints (8 GB VRAM laptop GPU).

However, an audit of the runtime architecture reveals notable systems-level gaps between the conceptual diagram (Fig. 1) and actual enforcement boundaries.

---

## 2. Systems and Security Objections

### Objection 3.1: Enforcement Boundaries and Runtime Bypasses
The paper claims that MemoryQuarantine "enforces a deterministic gate at the physical tool execution boundary."
- Where is this boundary physically located?
- In Python user-space runtimes, can an agent invocation bypass `ToolExecutor`? For example:
  1. What if an agent spawns a sub-agent or calls an internal helper directly?
  2. Does the task graph DAG executor route through `ToolExecutor`?
  3. Does the Scrapling web crawler enforce network boundaries?
If any tool or task path bypasses `ToolExecutor`, the security gate is toothless. The paper must explicitly prove that all physical action dispatchers route through the Guardian gate.

### Objection 3.2: Provenance Preservation in the Context Pipeline
Fig. 1 depicts a clean flow where provenance $\gamma(m)$ accompanies memories into the LLM context.
- In LLM prompting, memories are converted into text strings. Once in natural language, how does the system reliably map a tool proposal back to its supporting memory?
- What if the LLM blends information from two different memories (one trusted, one untrusted)?
- If the agent context contains three memories with $\gamma \in \{1.0, 0.50, 0.15\}$, which provenance governs the tool call?
The manuscript must formalize the multi-memory attribution resolution mechanism.

### Objection 3.3: TaskWAL Crash Consistency & Physical Recovery
In Section VI and Table IV, the paper mentions TaskWAL crash consistency ($N=500$ crash iterations).
- Is crash recovery verified against **physical OS subprocess termination** (`taskkill /F /PID` or `SIGKILL`), or merely deterministic in-memory exception loops?
- What happens if the workstation loses power while an uncommitted file mutation is in flight?
- Does TaskWAL enforce **fail-closed** file writes, or does a failure to append to the WAL allow the file write to proceed regardless?

### Objection 3.4: Shell Obfuscation and AST Limitations
The reversibility risk metric $\mathcal{R}(a)$ relies on AST pattern analysis.
- How does MemoryQuarantine handle obfuscated shell invocations (e.g., base64 encoding, environment variable indirection, PowerShell encoded commands)?
- If the LLM generates `python -c "exec(...)"` or `powershell -enc ...`, does $\mathcal{R}(a)$ evaluate to $1.00$ or does it default to a low-risk general script execution ($0.30$)?
This is an acute security limitation that must be acknowledged in the limitations section.

---

## 3. Required Systems Revisions
1. **Prove Comprehensive Routing**: Document how all execution channels (Task Graph, VisionAgent, Sub-agents) route through `ToolExecutor`.
2. **Formalize Working Set Attribution**: Specify the multi-memory attribution function (e.g., conservative minimum $\min_{i} \gamma_i$).
3. **Physical Crash Recovery Verification**: Provide evidence of real subprocess kill verification and fail-closed TaskWAL guarantees.
4. **Disclose Obfuscation Threat**: Acknowledge AST command parsing limitations as an explicit attack surface requiring future OS-level container isolation.

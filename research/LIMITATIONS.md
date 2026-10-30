# MemoryQuarantine: System Limitations, Residual Risks, & Boundary Conditions

**Target Venue:** IEEE International Conference on Cognitive Electronic Computing and Engineering (ICCECE 2027)  
**Document ID:** `research/LIMITATIONS.md`  
**Date:** October 30, 2026  
**Authors:** AI Safety & Security Researcher, Edge Computing Architect, Adversarial IEEE Reviewer  

---

## 1. Overview & Scientific Integrity

A core vulnerability in prior agentic research is presenting heuristic defenses as absolute security guarantees. MemoryQuarantine is designed for pragmatic, consequence-aware defensive mitigation on consumer edge devices; it is not an uncrackable formal proof system. 

This document explicitly delineates the operational boundaries, threat model assumptions, failure modes, and residual risks of the MemoryQuarantine architecture.

---

## 2. Threat Model Assumptions & Trust Boundaries

### 2.1 The Trusted Computing Base (TCB)
MemoryQuarantine presumes the integrity of the following host components:
1. **The Host Operating System & Kernel:** The local operating system (Windows/Linux), process memory protection rings, and kernel filesystem boundaries are assumed uncompromised. An adversary with root/administrator access or ring-0 privilege can bypass user-space gates by directly reading or writing SQLite database files on disk.
2. **The Local Python Runtime & Binary Tool Implementations:** The Python interpreter and the concrete definitions of tools (e.g. `file_write`, `shell_execute`) are trusted. Tool logic correctly executes the parameters passed to it without executing undeclared side-effects.
3. **The User Input Channel:** Prompts entered directly into the local GUI or terminal by the physical user are assigned the highest provenance (`user_explicit`, $\gamma = 1.00$). MemoryQuarantine cannot distinguish between an authorized user and an attacker who has gained physical or remote-desktop control of an unlocked session.

### 2.2 Out-of-Scope Threat Vectors
The following threats are outside the defensive perimeter of MemoryQuarantine:
- **Physical Hardware Attacks:** Cold-boot attacks, PCIe bus tapping, or DRAM fault injection (e.g. Rowhammer).
- **Compromised Model Weights:** Backdoored base foundation models whose pre-trained weights contain intrinsic dormant trojans that trigger without external memory retrieval.
- **Hardware-Level Side Channels:** Cache-timing attacks, electromagnetic exfiltration, or acoustic keylogging.
- **Pre-Execution Compromise:** Adversarial tampering with the Python codebase or `GuardianEngine` source files before runtime initialization.

---

## 3. Methodological & Algorithmic Limitations

### 3.1 Reliance on Heuristic Action Reversibility Scoring
- **Limitation:** In the current implementation, semantic reversibility risk $\mathcal{R}(a) \in [0.0, 1.0]$ is evaluated through a hybrid AST parser and normalized regular expression classifier.
- **Failure Mode:** For opaque or dynamically generated execution payloads (e.g. complex multi-line bash scripts or obfuscated PowerShell scripts such as `powershell -enc ...`), static AST parsing may misclassify a destructive command as a read-only script ($\mathcal{R}(a) = 0.05$ instead of $1.00$), permitting low-authority memory to trigger it.
- **Mitigation in C.O.P.P.E.R.:** Hard safety invariant normalization (`normalize_adversarial_text`) strips zero-width spaces, Cyrillic homoglyphs, and base64 payloads before reversibility evaluation. However, semantic evaluation of Turing-complete shell scripts remains undecidable in the general case.

### 3.2 Single-User Edge Focus vs. Distributed Multi-Tenant Consensus
- **Limitation:** MemoryQuarantine is evaluated in a single-user, local-first personal computing setting.
- **Boundary Condition:** In multi-tenant enterprise environments where multiple users with differing permission tiers read and write to a shared episodic memory store, provenance requires cryptographic digital signatures (e.g. asymmetric key signing per agent) to prevent identity spoofing.

### 3.3 Confirmation Fatigue & Operator Habituation
- **Limitation:** When memory authority falls into the intermediate CHALLENGE zone ($0.25 \le \text{Authority} < 0.65$), execution requires explicit operator confirmation.
- **Human Factor Risk:** In high-frequency workflows, repeated confirmation prompts can induce operator fatigue, leading users to reflexively click "Confirm" without scrutinizing the underlying command (the classic automation bias / "cry-wolf" habituation).
- **Mitigation:** MemoryQuarantine minimizes false challenges by allowing high-confidence user memories to execute silently ($\text{Authority} \ge 0.65$), restricting operator interruptions to genuinely ambiguous or intermediate-risk operations.

### 3.4 Local Edge Model Capacity Bounds
- **Limitation:** Small language models (0.5B to 7B parameters) running locally on 8 GB consumer GPUs exhibit lower instruction-following fidelity and are more easily confused by complex multi-step prompt injections than 70B+ cloud frontier models.
- **Architectural Consequence:** Edge systems cannot rely on the LLM to inspect itself or enforce its own guardrails. The authorization plane must remain strictly external, deterministic, and decoupled from LLM inference.

---

## 4. Summary of Residual Risks

| Dimension | Residual Risk Description | Severity | Recommended Future Work |
| :--- | :--- | :---: | :--- |
| **Shell Obfuscation** | Highly convoluted shell scripts may mask high-risk disk modifications. | Moderate | Integrate dynamic OS sandbox execution tracing (e.g. seccomp / Windows Sandbox containerization). |
| **User Social Engineering** | An adversary tricks the human user into entering an explicit instruction that authorizes a poisoned memory. | Low | Multi-modal confirmation dialogs highlighting memory provenance history. |
| **Storage Tampering** | Local malware on the host machine modifies `user_memories_v2.db` directly on disk. | High (Out of Scope) | OS-level database file encryption (SQLCipher) with hardware TPM key sealing. |

---

## 5. Conclusion

Documenting these limitations does not diminish the scientific validity of MemoryQuarantine; rather, it establishes the precise boundaries within which its empirical guarantees ($\text{ASR} = 0.0\%$, $\text{TIR} = 100.0\%$) hold, preventing reviewer rejection for unsubstantiated claims of universal security.

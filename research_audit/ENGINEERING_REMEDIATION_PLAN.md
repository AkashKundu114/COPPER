# Engineering Remediation Plan & Long-Term Roadmap

**Project:** C.O.P.P.E.R (Cognitive Operator, Privacy & Planning Execution Runtime)  
**Author:** Principal Software Architect & Reliability Engineering Team  
**Status:** ACTIVE REMEDIATION & LONG-TERM MILESTONES  

---

## 1. Phase 1: Completed Immediate Interventions (Cycle 1)

1. [x] **Repair Memory Provenance Propagation:** Forwarded paired provenance and confidence metadata in `BaseAgent.run()` and `stream()`.
2. [x] **Add Missing Imports:** Added `import re` in `base.py` and `from typing import Any` in `guardian.py`.
3. [x] **PowerShell Base64 UTF-16LE & Caret Deobfuscation:** Closed adversarial evasion holes in Guardian text normalizer.
4. [x] **Enforce Airgap on Science Tools:** Added `NetworkMode.OFFLINE_AIRGAP` check to `arxiv_search`.
5. [x] **Enforce Loopback on Scrapling Tools:** Restricted `scrapling_scrape` to local loopback under `NetworkMode.LOCAL_SERVICES`.
6. [x] **ContextEngine Active Facts Alias:** Connected `memory_manager.get_active_memories` to `get_relevant_structured_memories`.
7. [x] **Desktop Interaction Gating:** Intercepted shell command typing and system hotkeys in `VisionAgent`.

---

## 2. Phase 2: Medium-Term Hardening (Cycle 2)

1. [ ] **Global WAL Session for Standalone Chats:**
   - Bind a session-level `TaskWAL` instance during standalone REPL or WebSocket interactive chat so that direct agent tool calls are crash-rollable.
2. [ ] **Filesystem Sandbox Containment (`_get_allowed_roots`):**
   - Restrict write operations strictly to `DOCUMENTS_DIR` and a dedicated `workspace/` directory.
   - Prohibit writing to repository source files (`parents[5]`) and OS temporary roots.
3. [ ] **Host Shell Network Namespaces:**
   - On Windows, attach Windows Filtering Platform (WFP) rules or enforce Docker containerization for `shell_execute` when `OFFLINE_AIRGAP` is active.
4. [ ] **Cryptographic Operator Signatures:**
   - Replace unauthenticated `{"operator_confirmed": True}` booleans with signed confirmation tokens or asymmetric nonce verification.

---

## 3. Phase 3: Research & Architectural Evolution (Cycle 3)

1. [ ] **Adaptive Plasticity Bayesian Decay:**
   - Extend UMF-EDR to estimate per-domain prior confidence distributions based on user feedback cycles.
2. [ ] **Dynamic Reversibility Matrix:**
   - Compute fine-grained file entropy and system dependency graphs before executing destructive mutations.
3. [ ] **Formal Verification of Guardian Invariants:**
   - Formally verify that no reachable control-flow path in `ToolExecutor` executes a level $\ge 3$ action without either a verified hard-safety pass or an authenticated operator token.

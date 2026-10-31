# Comprehensive Execution Path & Tool Inventory: C.O.P.P.E.R

**Audited Git Commit:** `ed23f11` (+ surgical remediation on `main`)  
**Audit Date:** 2026-10-31  
**Audit Team:** Runtime Auditor, Security Auditor, Memory Engineer, Tool Execution Specialist, Red-Team Reviewer  

---

## 1. Agent Execution Path & Tool Gating Inventory

This table records every active agent in C.O.P.P.E.R, its dispatch mechanisms, tool execution routes, Guardian safety gating, MemoryQuarantine integration, and TaskWAL crash-logging status.

| Agent Name | Agent Enum (`AgentType`) | Execution Methods | Tool Invocation Route | ToolExecutor Enforced? | Guardian Gating Enforced? | Memory Provenance Forwarded? | TaskWAL Logging? | Verified Runtime Status |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| **ChatAgent** | `chat` | `run()`, `stream()` | Text only / No tools | N/A | Invariant check on prompt | ✅ Coupled (`_extract_memory_provenance`) | N/A | **VERIFIED IMPLEMENTED** |
| **CodingAgent** | `coding` | `run()`, `stream()` | XML `<tool_call>` tags | ✅ Yes (`tool_executor.execute`) | ✅ Safety Gate (`evaluate()`) | ✅ Forwarded in context | ✅ When under `TaskGraph` | **VERIFIED IMPLEMENTED** |
| **AutomationAgent** | `automation` | `run()`, `stream()` | XML `<tool_call>` tags | ✅ Yes (`tool_executor.execute`) | ✅ Safety Gate (`evaluate()`) | ✅ Forwarded in context | ✅ When under `TaskGraph` | **VERIFIED IMPLEMENTED** |
| **ReminderAgent** | `reminder` | `run()`, `stream()` | XML `<tool_call>` tags | ✅ Yes (`tool_executor.execute`) | ✅ Safety Gate (`evaluate()`) | ✅ Forwarded in context | ✅ When under `TaskGraph` | **VERIFIED IMPLEMENTED** |
| **ResearchAgent** | `research` | `run()`, `stream()` | XML `<tool_call>` tags | ✅ Yes (`tool_executor.execute`) | ✅ Safety Gate (`evaluate()`) | ✅ Forwarded in context | ✅ When under `TaskGraph` | **VERIFIED IMPLEMENTED** |
| **VisionAgent (IRIS)** | `vision` | `run()`, `stream()`, ReAct | Direct `screen_tools` calls | ⚠️ Hybrid (window/typing safety checked) | ✅ Explicit `evaluate_screen_action()` + `evaluate()` | N/A (Visual ReAct loop) | ❌ Direct OS interaction | **VERIFIED IMPLEMENTED (REMEDIATED)** |
| **PlannerAgent** | `planner` | `run()`, `stream()`, `decompose()` | Generates DAG JSON | N/A | Evaluates plan steps | ✅ Forwarded in context | N/A | **VERIFIED IMPLEMENTED** |
| **GuardianAgent** | `guardian` | `run()`, `stream()`, `evaluate()` | Guardian Engine API | N/A | Evaluates action safety | ✅ Evaluates authority formula | N/A | **VERIFIED IMPLEMENTED** |
| **WebSearchAgent** | `web_search` | `run()`, `stream()`, ReAct | `web_search()`, `web_fetch()` | ⚠️ Direct helper calls | ✅ Airgap & WAN loopback checked | ✅ Forwarded in context | N/A (Read-only network) | **VERIFIED IMPLEMENTED (REMEDIATED)** |
| **DocumentAgent** | `document` | `run()`, `stream()` | `document_service` calls | ⚠️ Direct service calls | ✅ Path containment checked | ✅ Forwarded in context | ⚠️ Uses service persistence | **VERIFIED IMPLEMENTED** |
| **ImageAgent** | `image` | `run()`, `stream()` | `diffusion_engine` calls | ⚠️ Direct engine calls | ✅ Path containment checked | ✅ Forwarded in context | N/A (Generative model) | **VERIFIED IMPLEMENTED** |
| **SelfModelAgent** | `self_model` | `run()`, `stream()`, reflection | Self-reflection / DB | N/A | Checked during reflection | ✅ Forwarded in context | N/A (ORM updates) | **VERIFIED IMPLEMENTED** |

---

## 2. Builtin Tool Inventory & Safety Gating Matrix

| Tool Name | Module Path | Guardian Level | Destructive? | Airgap Check Enforced? | TaskWAL Logging? | Path Sandboxing? |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| `file_write` | `app.ai.tools.builtin.file_tools` | Level 3 | ✅ Yes | N/A (Filesystem) | ✅ Logged via `current_wal` | ✅ `validate_safe_path()` |
| `file_delete` | `app.ai.tools.builtin.file_tools` | Level 3 | ✅ Yes | N/A (Filesystem) | ✅ Logged via `current_wal` | ✅ `validate_safe_path()` |
| `file_read` | `app.ai.tools.builtin.file_tools` | Level 0 | ❌ No | N/A (Filesystem) | ❌ Read-only | ✅ `validate_safe_path()` |
| `list_directory` | `app.ai.tools.builtin.file_tools` | Level 0 | ❌ No | N/A (Filesystem) | ❌ Read-only | ✅ `validate_safe_path()` |
| `file_exists` | `app.ai.tools.builtin.file_tools` | Level 0 | ❌ No | N/A (Filesystem) | ❌ Read-only | ✅ `validate_safe_path()` |
| `shell_execute` | `app.ai.tools.builtin.shell_tools` | Level 3 | ✅ Yes | ⚠️ Host OS dispatch | ⚠️ Action recorded | ❌ Unconfined shell |
| `python_execute` | `app.ai.tools.builtin.python_tools` | Level 2 | ⚠️ Code execution | ✅ Docker (`--network=none`) / Subprocess | ⚠️ Action recorded | ✅ Temp isolation |
| `web_search` | `app.ai.tools.builtin.web_tools` | Level 1 | ❌ No | ✅ Strict `OFFLINE_AIRGAP` check | ❌ Read-only network | N/A |
| `web_fetch` | `app.ai.tools.builtin.web_tools` | Level 1 | ❌ No | ✅ `OFFLINE_AIRGAP` + `LOCAL_SERVICES` WAN restriction | ❌ Read-only network | N/A |
| `scrapling_scrape` | `app.ai.tools.builtin.scrapling_tools` | Level 1 | ❌ No | ✅ `OFFLINE_AIRGAP` + `LOCAL_SERVICES` WAN restriction | ❌ Read-only network | N/A |
| `arxiv_search` | `app.ai.tools.builtin.science_tools` | Level 0 | ❌ No | ✅ `OFFLINE_AIRGAP` check enforced | ❌ Read-only network | N/A |
| `screenshot` | `app.ai.tools.builtin.screen_tools` | Level 0 | ❌ No | N/A (Desktop) | ❌ Read-only | N/A |
| `click` | `app.ai.tools.builtin.screen_tools` | Level 1 | ⚠️ Low impact | N/A (Desktop) | ❌ UI action | Window whitelist/blacklist |
| `double_click` | `app.ai.tools.builtin.screen_tools` | Level 1 | ⚠️ Low impact | N/A (Desktop) | ❌ UI action | Window whitelist/blacklist |
| `type_text` | `app.ai.tools.builtin.screen_tools` | Level 1 | ⚠️ Potential inject | N/A (Desktop) | ❌ UI action | ✅ Password + Command check |
| `hotkey` | `app.ai.tools.builtin.screen_tools` | Level 1 | ⚠️ High impact | N/A (Desktop) | ❌ UI action | ✅ System shortcut challenge |
| `scroll` | `app.ai.tools.builtin.screen_tools` | Level 0 | ❌ No | N/A (Desktop) | ❌ UI action | N/A |
| `wait` | `app.ai.tools.builtin.screen_tools` | Level 0 | ❌ No | N/A (Desktop) | ❌ Timing only | N/A |

---

## 3. Discrepancy & Bypasses Audit Log

1. **`BaseAgent.run()` Provenance Stripping (REMEDIATED)**:
   - *Previous Defect:* `run()` called `tool_executor.execute(context={"agent": self.name, "step": step + 1})`, omitting memory provenance metadata. Non-streaming execution allowed poisoned memories to bypass MemoryQuarantine.
   - *Remediation Applied:* Added `_extract_memory_provenance()` pairing memory provenance with confidence and forwarding them in `context` across both `run()` and `stream()`.
2. **Missing `import re` in `base.py` (REMEDIATED)**:
   - *Previous Defect:* `stream()` invoked `re.findall()` while `import re` was missing, triggering `NameError` whenever memory context was present.
   - *Remediation Applied:* Added `import re` at line 1 of `base.py`.
3. **PowerShell Base64 UTF-16LE Obfuscation (REMEDIATED)**:
   - *Previous Defect:* `normalize_adversarial_text()` only decoded UTF-8 base64. Standard PowerShell `-enc` (UTF-16LE) strings passed through undetected with embedded null bytes.
   - *Remediation Applied:* Updated normalizer to decode both UTF-8 and UTF-16LE, stripping null bytes and matching against safety triggers.
4. **CMD Caret Obfuscation (REMEDIATED)**:
   - *Previous Defect:* `d^e^l /f /q` evaded regex token checks.
   - *Remediation Applied:* Normalizer removes `^` characters before pattern matching.
5. **Airgap WAN Leak in `arxiv_search` (REMEDIATED)**:
   - *Previous Defect:* Direct `httpx.AsyncClient` query ignored `NetworkMode.OFFLINE_AIRGAP`.
   - *Remediation Applied:* Enforced `get_current_network_mode() == NetworkMode.OFFLINE_AIRGAP` check raising `NetworkEgressForbiddenError`.
6. **`ContextEngine` Method Missing on `MemoryManager` (REMEDIATED)**:
   - *Previous Defect:* `context_engine.py` called `memory_manager.get_active_memories(db, limit=5)`, which did not exist on `MemoryManager`, causing active facts to fail silently.
   - *Remediation Applied:* Added `get_active_memories = get_relevant_structured_memories` alias.
